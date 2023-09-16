import os
import re
import sys
from typing import Any
from django.db import connections
from django.apps import apps
from django.core.management.commands.migrate import (
    Command as BaseMigrateCommand,
)
from django.db.migrations.operations.fields import RemoveField
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
            targets = [
                key for key in executor.loader.graph.leaf_nodes() if key[0] == app_label
            ]
        else:
            targets = executor.loader.graph.leaf_nodes()

        plan = executor.migration_plan(targets)
        for migration, is_backwards in plan:
            if not is_backwards:
                self.check_migration_safety(migration)

        return super().handle(*args, **options)

    def check_migration_safety(self, migration: Migration):
        for operation in migration.operations:
            if isinstance(operation, RemoveField):
                self.raise_or_warn(operation=operation, migration=migration)

    def raise_or_warn(self, migration: Migration, operation: Operation):
        safety_assured = getattr(migration, "safety_assured", False)

        error = UnsafeMigrationError(operation=operation, migration=migration)
        if safety_assured:
            logger.warn(error.message)
            return
        raise error
