from django.db.migrations.operations import (
    AddConstraint,
    AddField,
    AddIndex,
    AlterField,
    RemoveField,
    RemoveIndex,
    RenameField,
)
from django.db.migrations import Migration
from django.db.models import ForeignKey

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
    "_check_make_nullable",
]


def _check_add_field(operation: AddField, **kwargs):
    db_default = getattr(operation.field, "db_default", None)
    db_default_set = (
        db_default is not None
        and getattr(db_default, "__name__", None) != "NOT_PROVIDED"
    )

    if not (operation.field.null or db_default_set):
        raise UnsafeMigrationError(
            migration=kwargs["migration"],
            operation=operation,
            extra_info=INFO_MESSAGES["add_non_nullable_field"],
        )

    if kwargs.get("pg_major_version") and isinstance(operation.field, ForeignKey) and operation.field.db_constraint:
        raise UnsafeMigrationError(
            migration=kwargs["migration"],
            operation=operation,
            extra_info=INFO_MESSAGES["add_foreign_key"],
        )


def _check_alter_field(operation: AlterField, **kwargs):
    state = kwargs["project_state"]
    migration = kwargs["migration"]
    pg_version = kwargs["pg_major_version"]
    django_version = kwargs["django_version"]

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
    if operation.field.null:
        _check_make_nullable(
            operation=operation,
            old_field_state=old_field_state,
            migration=migration,
            apps=kwargs["apps"],
            check_dms_redshift_safety=kwargs["check_dms_redshift_safety"],
            django_major_version=django_version[0],
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


def _check_make_nullable(
    operation: AlterField,
    migration: Migration,
    old_field_state,
    check_dms_redshift_safety: bool,
    apps,
    django_major_version: int,
):
    model = apps.get_model(migration.app_label, operation.model_name)
    if not _model_check_dms_redshift_safety(
        model=model, check_dms_redshift_safety=check_dms_redshift_safety
    ):
        return

    if django_major_version >= 5:
        existing_db_default = getattr(old_field_state, "db_default", None)
        existing_db_default_set = (
            existing_db_default is not None
            and getattr(existing_db_default, "__name__", None) != "NOT_PROVIDED"
        )

        operation_db_default = getattr(operation.field, "db_default", None)
        operation_db_default_set = (
            operation_db_default is not None
            and getattr(operation_db_default, "__name__", None) != "NOT_PROVIDED"
        )
        db_default_safe = operation_db_default_set or existing_db_default_set
    else:
        # no easy way to check if theres a db column default otherwise
        db_default_safe = False

    if (
        old_field_state.null is False
        and operation.field.null is True
        and not db_default_safe
    ):
        raise UnsafeMigrationError(
            migration=migration,
            operation=operation,
            extra_info=INFO_MESSAGES["alter_field_make_nullable_dms_redshift"],
        )


def _model_check_dms_redshift_safety(model, check_dms_redshift_safety: bool):
    return getattr(
        model, "STRONG_MIGRATIONS_CHECK_DMS_REDSHIFT_SAFETY", check_dms_redshift_safety
    )
