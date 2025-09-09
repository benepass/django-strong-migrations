import logging
from typing import Optional

from django.db.migrations import Migration
from django.db.migrations.operations import (
    AddConstraint,
    AddField,
    AddIndex,
    AlterField,
    RemoveField,
    RemoveIndex,
    RenameField,
)
from django.db.migrations.state import ProjectState

from ..errors import UnsafeMigrationError
from .checks import (
    _check_add_constraint,
    _check_add_field,
    _check_add_index,
    _check_alter_field,
    _check_remove_field,
    _check_remove_index,
    _check_rename_field,
)

logger = logging.getLogger(__name__)

OPERATION_CHECKS = {
    AddConstraint: _check_add_constraint,
    AddIndex: _check_add_index,
    AddField: _check_add_field,
    AlterField: _check_alter_field,
    RenameField: _check_rename_field,
    RemoveField: _check_remove_field,
    RemoveIndex: _check_remove_index,
}


def check_migration_safety(
    apps: any,
    migration: Migration,
    pg_major_version: Optional[int],
    check_dms_redshift_safety: bool,
    project_state: ProjectState,
    django_version: tuple,
) -> bool:
    for operation in migration.operations:
        check_method = OPERATION_CHECKS.get(type(operation))
        if check_method:
            try:
                check_method(
                    operation=operation,
                    pg_major_version=pg_major_version,
                    project_state=project_state,
                    apps=apps,
                    check_dms_redshift_safety=check_dms_redshift_safety,
                    migration=migration,
                    django_version=django_version,
                )
            except UnsafeMigrationError as error:
                if getattr(operation, "safety_assured", False):
                    operation_name = operation.__class__.__name__
                    logger.warn(
                        (
                            "operation marked as safe: "
                            f"(migration: {migration.name}, "
                            f"operation: {operation_name})"
                        )
                    )
                    return
                raise error

    return True
