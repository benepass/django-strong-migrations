from typing import Optional
import pytest
import os
import subprocess
from importlib import import_module
from tests.mocks import MockProjectState, MockModelState
from strong_migrations.check_safety import check_migration_safety
from strong_migrations.errors import UnsafeMigrationError
from strong_migrations.check_safety.info_messages import INFO_MESSAGES
import re
from django.db import models
from django.apps.registry import apps


@pytest.fixture()
def test_app_path(test_path):
    return os.path.join(test_path, "test_project")


@pytest.fixture()
def test_path():
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture()
def run_test_app_db(test_app_path):
    def _run(command: str, appname="testapp", postgres: bool = False):
        env_vars = os.environ.copy()
        args = command.split(" ")

        if postgres:
            env_vars["DB"] = "postgres"

        subprocess.run(
            args=["python", "manage.py", "migrate", appname, "zero"],
            cwd=test_app_path,
            env=env_vars,
        )
        result = subprocess.run(
            args=args,
            cwd=test_app_path,
            env=env_vars,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        yield result
        subprocess.run(
            args=["python", "manage.py", "migrate", appname, "zero"],
            cwd=test_app_path,
            env=env_vars,
        )

    return _run


@pytest.fixture
def make_migration():
    def _factory(migration_name: str):
        return import_module(f"tests.fixtures.migrations.{migration_name}").Migration

    return _factory


@pytest.fixture
def make_project_state():
    def _factory(model):
        model = MockModelState.from_model(model=model)

        return MockProjectState(models={(model.app_label, model.name_lower): model})

    return _factory


@pytest.fixture
def make_user_model():
    def _factory(email_index: bool = False):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.mocks.mock_settings")

        class User(models.Model):
            id = models.BigAutoField(primary_key=True)
            email = models.EmailField(null=True, db_index=email_index)

            class Meta:
                app_label = "mock_app"

        return User

    return _factory


@pytest.fixture
def setup_migration_state(
    make_migration, make_project_state, make_user_model, mock_app
):
    def _factory(migration_name: str):
        user_model = make_user_model()
        pre_migration_state = make_project_state(model=user_model)
        migration = make_migration(migration_name=migration_name)
        return migration, pre_migration_state

    return _factory


@pytest.fixture
def assert_unsafe(setup_migration_state):
    def _factory(
        migration_name: str,
        info_message: Optional[str] = None,
        pg_version: Optional[int] = None,
    ):
        info_message = info_message or migration_name
        migration, pre_migration_state = setup_migration_state(
            migration_name=migration_name
        )
        with pytest.raises(
            UnsafeMigrationError, match=re.escape(INFO_MESSAGES[info_message])
        ):
            check_migration_safety(
                migration=migration,
                pg_major_version=pg_version,
                project_state=pre_migration_state,
            )

    return _factory


@pytest.fixture
def assert_safe(setup_migration_state):
    def _factory(
        migration_name: str,
        pg_version: Optional[int] = None,
    ):
        migration, pre_migration_state = setup_migration_state(
            migration_name=migration_name
        )
        assert (
            check_migration_safety(
                migration=migration,
                pg_major_version=pg_version,
                project_state=pre_migration_state,
            )
            is None
        )

    return _factory


@pytest.fixture
def mock_app():
    apps.populate(installed_apps=["tests.mocks.mock_app.apps"])
    yield
    apps.all_models = {"mock_app": {}}
    apps.app_configs = {}


@pytest.fixture(scope="function", autouse=True)
def _dj_autoclear_mailbox() -> None:
    # Override the `_dj_autoclear_mailbox` test fixture in `pytest_django`.
    pass
