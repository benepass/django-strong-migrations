from strong_migrations.errors import InvalidConfigurationError

DEFAULT_TIMEOUT = "0s"


def set_lock_timeout_from_settings(*, connection, settings, pg_version):
    lock_timeout = getattr(settings, "STRONG_MIGRATIONS_LOCK_TIMEOUT", None)
    if lock_timeout and not pg_version:
        raise InvalidConfigurationError("cannot set lock timeout on non-pg databases")
    if not lock_timeout:
        return
    set_lock_timeout(connection=connection, timeout=lock_timeout)


def reset_lock_timeout_from_settings(*, connection, settings):
    lock_timeout = getattr(settings, "STRONG_MIGRATIONS_LOCK_TIMEOUT", None)
    if not lock_timeout:
        return
    set_lock_timeout(connection=connection, timeout=DEFAULT_TIMEOUT)


def set_lock_timeout(*, connection, timeout: str):
    with connection.cursor() as cursor:
        cursor.execute(f"set lock_timeout to '{timeout}';")
