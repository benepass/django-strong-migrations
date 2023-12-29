import pytest
import os
import subprocess


@pytest.fixture()
def test_app_path(test_path):
    return os.path.join(test_path, "test_project")


@pytest.fixture()
def test_path():
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture()
def run_test_app_db(test_app_path):
    def _run(command: str, postgres: bool = False):
        env_vars = os.environ.copy()
        args = command.split(" ")

        if postgres:
            env_vars["DB"] = "postgres"

        subprocess.run(
            args=["python", "./manage.py", "migrate", "testapp", "0001"],
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
            args=["python", "./manage.py", "migrate", "testapp", "0001"],
            cwd=test_app_path,
            env=env_vars,
        )

    return _run
