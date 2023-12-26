import os
import re
import sys
from typing import Any
from django.db import connections
from django.apps import apps
from django.core.management.commands.migrate import (
    Command as BaseMigrateCommand,
)
from django.db.migrations.operations.fields import (
    RemoveField,
    RenameField,
)
from django.db.migrations.operations.models import AddConstraint, AddIndex, RemoveIndex
from django.db.migrations.operations.base import Operation
from django.db.migrations.migration import Migration
from django.db.migrations.loader import AmbiguityError
from django.core.management.base import CommandError
from django.db.migrations.executor import MigrationExecutor
from strong_migrations.errors.unsafe_migration_error import UnsafeMigrationError
import logging

logger = logging.getLogger(__name__)


class Command(BaseMigrateCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        database = options["database"]
        if not options["skip_checks"]:
            self.check(databases=[database])

        self.verbosity = options["verbosity"]
        self.interactive = options["interactive"]

        # Get the database we're operating from
        connection = connections[database]

        # Hook for backends needing any database preparation
        connection.prepare_database()
        # Work out which apps have migrations and which do not
        executor = MigrationExecutor(connection, self.migration_progress_callback)

        if options["app_label"] and options["migration_name"]:
            app_label = options["app_label"]
            migration_name = options["migration_name"]
            if migration_name == "zero":
                targets = [(app_label, None)]
            else:
                try:
                    migration = executor.loader.get_migration_by_prefix(
                        app_label, migration_name
                    )
                except AmbiguityError:
                    raise CommandError(
                        "More than one migration matches '%s' in app '%s'. "
                        "Please be more specific." % (migration_name, app_label)
                    )
                except KeyError:
                    raise CommandError(
                        "Cannot find a migration matching '%s' from app '%s'."
                        % (migration_name, app_label)
                    )
                targets = [(app_label, migration.name)]
            target_app_labels_only = False
        elif options["app_label"]:
            app_label = options["app_label"]
            targets = [
                key for key in executor.loader.graph.leaf_nodes() if key[0] == app_label
            ]
        else:
            targets = executor.loader.graph.leaf_nodes()

        # users can determine which migration to start checking safety of from each app
        # we need to mark all migrations prior to the selected migration as "applied"
        # so that our migration plan no longer includes them
        starting_targets = []
        for target in targets:
            app_label, _target = target
            check_from = getattr(
                apps.get_app_config(app_label=app_label),
                "check_safe_migrations_from",
                None,
            )
            if not check_from:
                continue
            try:
                executor.loader.get_migration(
                    app_label=app_label, name_prefix=check_from
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load starting migration {check_from}")
            starting_targets.append((app_label, check_from))

        starting_plan = None
        if starting_targets:
            starting_plan = executor.migration_plan(targets=starting_targets)
            for migration, backwards in starting_plan:
                if not backwards:
                    executor.recorder.record_applied(
                        app=migration.app_label, name=migration.name
                    )
            executor.loader.build_graph()

        # now we can check the actual migrations we need
        plan = executor.migration_plan(targets)

        for migration, is_backwards in plan:
            if not is_backwards:
                self.check_migration_safety(migration)

        # now we need to reset our migration state so that the real migrate command
        # actually runs everything it needs
        if starting_targets:
            for migration, backwards in starting_plan:
                if not backwards:
                    executor.recorder.record_unapplied(
                        app=migration.app_label, name=migration.name
                    )
                executor.loader.build_graph()

        executor.migration_plan(targets)
        return super().handle(*args, **options)

    def check_migration_safety(self, migration: Migration):
        for operation in migration.operations:
            if type(operation) in [
                RemoveField,
                RenameField,
                AddConstraint,
                AddIndex,
                RemoveIndex,
            ]:
                self.raise_or_warn(operation=operation, migration=migration)

    def raise_or_warn(self, migration: Migration, operation: Operation):
        safety_assured = getattr(migration, "safety_assured", False)

        error = UnsafeMigrationError(operation=operation, migration=migration)
        if safety_assured:
            logger.warn(error.message)
            return
        raise error
