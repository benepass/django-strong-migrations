import pytest
from threading import Thread

from django.db import connection
import os
from asgiref.sync import sync_to_async


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


def test_migrate_command_with_check_safe_migrations_from(run_test_app_db):
    # this app has check_safe_migrations_from = "0002_rename_test_field"
    # so this migration should succeed even though its unsafe
    for result in run_test_app_db(
        command="python manage.py migrate legacyapp 0002", appname="legacyapp"
    ):
        assert result.returncode == 0
        assert "Applying legacyapp.0002_rename_test_field... OK" in result.stdout


def test_migrate_command_with_safety_assured(run_test_app_db):
    # this migration has safety_assured = True, so should succeed
    for result in run_test_app_db(
        command="python manage.py migrate legacyapp 0003", appname="legacyapp"
    ):
        assert result.returncode == 0
        assert (
            "Applying legacyapp.0003_rename_test_field_marked_safe... OK"
            in result.stdout
        )


def run_test_migrate_command_with_skip_safety_checks(run_test_app_db):
    # this migration is unsafe and should fail
    for result in run_test_app_db(
        command="python manage.py migrate legacyapp 0004", appname="legacyapp"
    ):
        assert result.returncode == 1

        assert "UNSAFE MIGRATION DETECTED" in result.stderr

    # the unsafe migration should pass if we use --skip-safety-checks
    for result in run_test_app_db(
        command="python manage.py migrate legacyapp 0004 --skip-safety-checks",
        appname="legacyapp",
    ):
        assert result.returncode == 0
        assert "Applying testapp.0004_rename_test_field_unsafe... OK" in result.stdout


def hold_lock_on_legacymodel():
    original_settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", None)
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.test_project.test_project.settings"
    try:
        # STRONG_MIGRATIONS_LOCK_TIMEOUT is set to 1s in the test app
        # this sleeps for 2s, locking the table
        with connection.cursor() as cursor:
            cursor.execute(
                """
                    begin;
                    lock table legacyapp_legacymodel in ACCESS EXCLUSIVE MODE;
                    select pg_sleep(2);
                    commit;
                    """
            )
    finally:
        if not original_settings_module:
            os.environ.pop("DJANGO_SETTINGS_MODULE")
        else:
            os.environ["DJANGO_SETTINGS_MODULE"] = original_settings_module


def test_migrate_with_lock_timeout(run_test_app_db):
    for result in run_test_app_db(
        command="python manage.py migrate legacyapp 0001",
        appname="legacyapp",
        postgres=True,
        reset_after=False,
    ):
        assert result.returncode == 0

    Thread(target=hold_lock_on_legacymodel).start()

    for result in run_test_app_db(
        command="python manage.py migrate legacyapp 0003",
        appname="legacyapp",
        postgres=True,
        reset_before=False,
    ):
        assert result.returncode == 1

        assert "canceling statement due to lock timeout" in result.stderr
