class UnsafeMigrationError(Exception):
    def __init__(
        self, *args: object, migration=None, operation=None, extra_info=None
    ) -> None:
        self.operation = operation
        self.migration = migration
        self.extra_info = extra_info
        self.message = self.resolve_message(
            operation=operation, migration=migration, extra_info=extra_info
        )
        super().__init__(self.message)

    def resolve_message(self, operation=None, migration=None, extra_info=None):
        migration_name = migration.name if migration else None
        operation_name = operation.__class__.__name__ if operation else None
        return f"""

=======================

UNSAFE MIGRATION DETECTED:

- migration: {migration_name}
- operation: {operation_name}

{extra_info}

Please see the documentation at https://github.com/benepass/django-strong-migrations#readme
"""
