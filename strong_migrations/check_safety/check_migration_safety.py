import logging
from typing import Optional

from django.db.migrations import Migration
from django.db.migrations.operations import (
    AddConstraint,
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
    AlterField: _check_alter_field,
    RenameField: _check_rename_field,
    RemoveField: _check_remove_field,
    RemoveIndex: _check_remove_index,
}


def check_migration_safety(
    migration: Migration,
    pg_major_version: Optional[int],
    project_state: ProjectState,
):
    for operation in migration.operations:
        check_method = OPERATION_CHECKS.get(type(operation))
        if check_method:
            try:
                return check_method(
                    operation=operation,
                    pg_major_version=pg_major_version,
                    project_state=project_state,
                    migration=migration,
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
