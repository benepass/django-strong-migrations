def test_check_migration_safety_add_constraint_without_postgres(assert_safe):
    assert_safe("add_constraint", pg_version=None)


def test_check_migration_safety_add_constraint_postgres(assert_unsafe):
    assert_unsafe(
        migration_name="add_constraint",
        pg_version=13,
    )


def test_check_migration_safety_add_index_without_postgres(assert_safe):
    assert_safe("add_index")


def test_check_migration_safety_add_index_with_postgres(assert_unsafe):
    assert_unsafe("add_index", pg_version=13)


def test_check_migration_safety_alter_field_add_index_without_postgres(assert_safe):
    assert_safe(migration_name="alter_field_add_index", pg_version=None)


def test_check_migration_safety_alter_field_add_index_with_postgres(assert_unsafe):
    assert_unsafe(
        migration_name="alter_field_add_index",
        info_message="add_index",
        pg_version=13,
    )


def test_check_migration_safety_alter_field_make_nullable_with_default_with_check_dms_redshift_replication(
    assert_safe, django_version
):
    if django_version[0] >= 5:
        assert_safe(
            migration_name="alter_field_with_default_make_nullable",
            check_dms_redshift_safety=True,
        )


def test_check_migration_safety_alter_field_make_nullable_with_check_dms_redshift_replication(
    assert_unsafe,
):
    assert_unsafe(
        migration_name="alter_field_without_default_make_nullable",
        info_message="alter_field_make_nullable_dms_redshift",
        check_dms_redshift_safety=True,
    )


def test_check_migration_safety_alter_field_make_nullable_with_check_dms_redshift_replication_with_operation_db_default(
    assert_safe, django_version
):
    if django_version[0] >= 5:
        assert_safe(
            migration_name="alter_field_without_default_make_nullable_with_db_default",
            check_dms_redshift_safety=True,
        )


def test_check_migration_safety_alter_field_make_nullable_without_check_dms_redshift_replication(
    assert_safe,
):
    assert_safe(
        migration_name="alter_field_without_default_make_nullable",
        check_dms_redshift_safety=False,
    )


def test_check_migration_safety_alter_field_make_nullable_without_default_with_check_dms_redshift_replication_but_disabled_model(
    assert_safe, mock_app
):
    assert_safe(
        migration_name="alter_field_without_default_make_nullable",
        check_dms_redshift_safety=True,
        model_kwargs={"check_dms_redshift_safety": False},
    )


def test_check_migration_safety_rename_field(assert_unsafe):
    assert_unsafe("rename_field")


def test_check_migration_safety_remove_field(assert_unsafe):
    assert_unsafe("remove_field")


def test_check_migration_safety_remove_index_without_postgres(assert_safe):
    assert_safe(migration_name="remove_index", pg_version=None)


def test_check_migration_safety_remove_index_with_postgres(assert_unsafe):
    assert_unsafe(migration_name="remove_index", pg_version=13)


def test_check_migration_safety_add_non_nullable_field(assert_unsafe):
    assert_unsafe(migration_name="add_non_nullable_field")


def test_check_migration_safety_add_non_nullable_field_with_jsonb_db_default(
    assert_safe, django_version, assert_unsafe
):
    if django_version[0] >= 5:
        assert_safe(migration_name="add_non_nullable_field_with_jsonb_default")


def test_check_migration_safety_add_nullable_field(assert_safe):
    assert_safe(migration_name="add_nullable_field")


def test_check_migration_safety_add_nullable_foreign_key_without_postgres(assert_safe):
    assert_safe(migration_name="add_nullable_foreign_key", pg_version=None)


def test_check_migration_safety_add_nullable_foreign_key_with_postgres(assert_unsafe):
    assert_unsafe(
        migration_name="add_nullable_foreign_key",
        info_message="add_foreign_key",
        pg_version=13,
    )


def test_check_migration_safety_multiple_operations(assert_unsafe):
    assert_unsafe(
        migration_name="multiple_operations", info_message="add_non_nullable_field"
    )
