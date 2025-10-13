import logging
import re
from typing import Any, Optional

from django import VERSION as DJANGO_VERSION
from django.apps import apps
from django.conf import settings
from django.core.management.base import CommandError, CommandParser
from django.core.management.commands.migrate import Command as BaseMigrateCommand
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import AmbiguityError

from strong_migrations.check_safety import check_migration_safety
from strong_migrations.set_lock_timeout import (
    set_lock_timeout_from_settings,
    reset_lock_timeout_from_settings,
)

logger = logging.getLogger(__name__)


class Command(BaseMigrateCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--skip-strong-migrations",
            action="store_true",
            help="skip django-strong-migration checks",
        )
        return super().add_arguments(parser)

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        database = options["database"]
        if not options["skip_checks"]:
            self.check(databases=[database])

        if options["skip_strong_migrations"]:
            return super().handle(*args, **options)

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
        project_check_dms_redshift_safety = getattr(
            settings, "STRONG_MIGRATIONS_CHECK_DMS_REDSHIFT_SAFETY", False
        )
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
                raise RuntimeError(
                    f"Failed to load starting migration {check_from}"
                ) from e
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
        pre_migrate_state = executor._create_project_state(with_applied_migrations=True)

        pg_version = self._pg_major_version(connection=connection)
        for migration, is_backwards in plan:
            if not is_backwards:
                app_dms_redshift_safety = getattr(
                    apps.get_app_config(app_label=migration.app_label),
                    "check_dms_safety",
                    project_check_dms_redshift_safety,
                )

                check_migration_safety(
                    apps=apps,
                    migration=migration,
                    project_state=pre_migrate_state,
                    pg_major_version=pg_version,
                    check_dms_redshift_safety=app_dms_redshift_safety,
                    django_version=DJANGO_VERSION,
                )
                for operation in migration.operations:
                    operation.state_forwards(migration.app_label, pre_migrate_state)

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

        set_lock_timeout_from_settings(
            connection=connection, settings=settings, pg_version=pg_version
        )
        result = super().handle(*args, **options)
        reset_lock_timeout_from_settings(connection=connection, settings=settings)
        return result

    def _pg_major_version(self, connection) -> int or None:
        """
        returns None if db connection is not a postgres connection
        major version number otherwise
        """
        if connection.settings_dict.get("ENGINE") != "django.db.backends.postgresql":
            return None
        try:
            # unfortunately, connection.cursor().connection.server_version does not work
            # with psycopg 3, which is required for python 3.11+
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                raw_version = cursor.fetchone()
            if not raw_version:
                raise Exception("could not find version number")
            match = re.search("PostgreSQL (\d+)\.\d{1,}", raw_version[0])
            if not match:
                raise Exception(
                    f"could not find version number from verson string {raw_version[0]}"
                )
            return int(match.group(1))
        except Exception as error:
            logger.warning(
                "strong_migrations could not determine postgres version number"
            )
            logger.warning(error)
            return
