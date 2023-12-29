from strong_migrations.errors import UnsafeMigrationError
from strong_migrations.check_safety.info_messages import INFO_MESSAGES

from django.db.migrations.operations import (
    AddConstraint,
    AddIndex,
    AlterField,
    RenameField,
    RemoveField,
    RemoveIndex,
)


def _check_alter_field(operation: AlterField, **kwargs):
    state = kwargs["project_state"]
    migration = kwargs["migration"]
    pg_version = kwargs["pg_major_version"]

    old_model_state = state.models[(migration.app_label, operation.model_name)]
    if old_model_state:
        old_field_state = old_model_state.fields.get(operation.name)
    else:
        old_field_state = None

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

    if not old_model_state:
        # if the model hadn't previously existed in the db
        # we don't need to worry about an index locking the table
        # since it isn't in use or populated yet
        return

    if (
        pg_version
        and (old_field_state is None or old_field_state.db_index is False)
        and operation.field.db_index is True
    ):
        raise UnsafeMigrationError(
            migration=migration,
            operation=operation,
            extra_info=INFO_MESSAGES["pg_alter_field_add_index"],
        )


def _check_remove_field(operation: RemoveField, **kwargs):
    pass


def _check_rename_field(operation: RenameField, **kwargs):
    pass


def _check_add_constraint(operation: AddConstraint, **kwargs):
    pass


def _check_add_index(operation: AddIndex, **kwargs):
    pass


def _check_remove_index(operation: RemoveIndex, **kwargs):
    pass
