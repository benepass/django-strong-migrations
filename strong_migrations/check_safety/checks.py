from django.db.migrations.operations import (
    AddConstraint,
    AddField,
    AddIndex,
    AlterField,
    RemoveField,
    RemoveIndex,
    RenameField,
)
from strong_migrations.check_safety.info_messages import INFO_MESSAGES
from strong_migrations.errors import UnsafeMigrationError

__all__ = [
    "_check_alter_field",
    "_check_add_field",
    "_check_remove_field",
    "_check_rename_field",
    "_check_add_constraint",
    "_check_add_index",
    "_check_remove_index",
]


def _check_add_field(operation: AddField, **kwargs):
    db_default = getattr(operation.field, "db_default", None)
    db_default_set = (
        db_default is not None
        and getattr(db_default, "__name__", None) != "NOT_PROVIDED"
    )

    if operation.field.null or db_default_set:
        return
    raise UnsafeMigrationError(
        migration=kwargs["migration"],
        operation=operation,
        extra_info=INFO_MESSAGES["add_non_nullable_field"],
    )


def _check_alter_field(operation: AlterField, **kwargs):
    state = kwargs["project_state"]
    migration = kwargs["migration"]
    pg_version = kwargs["pg_major_version"]

    old_model_state = state.models[(migration.app_label, operation.model_name)]
    old_field_state = old_model_state.fields.get(operation.name)

    if operation.field.db_index is True:
        _check_alter_field_index(
            operation=operation,
            old_model_state=old_model_state,
            old_field_state=old_field_state,
            pg_version=pg_version,
            migration=migration,
        )


def _check_alter_field_index(
    operation: AlterField, old_model_state, old_field_state, pg_version, migration
):
    if not pg_version:
        return

    if (
        pg_version
        and old_field_state.db_index is False
        and operation.field.db_index is True
    ):
        raise UnsafeMigrationError(
            migration=migration,
            operation=operation,
            extra_info=INFO_MESSAGES["add_index"],
        )


def _check_remove_field(operation: RemoveField, **kwargs):
    raise UnsafeMigrationError(
        migration=kwargs["migration"],
        operation=operation,
        extra_info=INFO_MESSAGES["remove_field"],
    )


def _check_rename_field(operation: RenameField, **kwargs):
    raise UnsafeMigrationError(
        migration=kwargs["migration"],
        operation=operation,
        extra_info=INFO_MESSAGES["rename_field"],
    )


def _check_add_constraint(operation: AddConstraint, **kwargs):
    if not kwargs.get("pg_major_version"):
        return
    raise UnsafeMigrationError(
        migration=kwargs["migration"],
        operation=operation,
        extra_info=INFO_MESSAGES["add_constraint"],
    )


def _check_add_index(operation: AddIndex, **kwargs):
    if not kwargs.get("pg_major_version"):
        return
    raise UnsafeMigrationError(
        migration=kwargs["migration"],
        operation=operation,
        extra_info=INFO_MESSAGES["add_index"],
    )


def _check_remove_index(operation: RemoveIndex, **kwargs):
    if not kwargs.get("pg_major_version"):
        return
    raise UnsafeMigrationError(
        migration=kwargs["migration"],
        operation=operation,
        extra_info=INFO_MESSAGES["remove_index"],
    )
