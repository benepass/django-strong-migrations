def test_migrate_command_with_safe_migrations(run_test_app_db, test_app_path):
    for result in run_test_app_db(command="python manage.py migrate testapp 0002"):
        assert result.returncode == 0
        assert "Applying testapp.0002_add_email... OK" in result.stdout


def test_migrate_command_with_unsafe_migrations_for_pg_with_sqllite(
    run_test_app_db, test_app_path
):
    for result in run_test_app_db(command="python manage.py migrate testapp 0003"):
        assert result.returncode == 0
        assert "Applying testapp.0003_index_email... OK" in result.stdout


def test_migrate_command_with_unsafe_migrations_for_pg_with_pg(
    run_test_app_db, test_app_path
):
    for result in run_test_app_db(
        command="python manage.py migrate testapp 0003", postgres=True
    ):
        assert result.returncode == 1

        assert "UNSAFE MIGRATION DETECTED" in result.stderr
