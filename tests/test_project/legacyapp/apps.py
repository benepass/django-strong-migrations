from django.apps import AppConfig


class LegacyappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "legacyapp"

    check_safe_migrations_from = "0002_rename_test_field"
