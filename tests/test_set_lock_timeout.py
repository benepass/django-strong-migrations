import pytest

from strong_migrations.set_lock_timeout import (
    set_lock_timeout_from_settings,
    reset_lock_timeout_from_settings,
)
from strong_migrations.errors import InvalidConfigurationError


@pytest.mark.parametrize("timeout, should_execute", (("2s", True), (None, False)))
def test_set_lock_timeout_from_settings_with_pg_db(
    timeout, should_execute, mocker, mock_connection
):
    class Settings:
        STRONG_MIGRATIONS_LOCK_TIMEOUT = timeout

    execute = mocker.patch("tests.mocks.mock_cursor_wrapper.MockCursorWrapper.execute")
    set_lock_timeout_from_settings(
        settings=Settings(), connection=mock_connection, pg_version=12
    )
    if should_execute:
        execute.assert_called_with(f"set lock_timeout to '{timeout}';")
    else:
        execute.assert_not_called()


@pytest.mark.parametrize("timeout, should_raise", (("2s", True), (None, False)))
def test_set_lock_timeout_from_settings_without_pg(
    timeout, should_raise, mock_connection
):
    class Settings:
        STRONG_MIGRATIONS_LOCK_TIMEOUT = timeout

    if should_raise:
        with pytest.raises(
            InvalidConfigurationError,
            match="cannot set lock timeout on non-pg databases",
        ):
            set_lock_timeout_from_settings(
                settings=Settings(), connection=mock_connection, pg_version=None
            )
    else:
        assert (
            set_lock_timeout_from_settings(
                settings=Settings(), connection=mock_connection, pg_version=None
            )
            is None
        )
