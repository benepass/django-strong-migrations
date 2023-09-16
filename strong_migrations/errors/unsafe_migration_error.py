from textwrap import dedent


class UnsafeMigrationError(Exception):
    def __init__(self, *args: object, migration=None, operation=None) -> None:
        self.operation = operation
        self.migration = migration
        self.message = self.resolve_message(operation=operation, migration=migration)
        super().__init__(self.message)

    def resolve_message(self, operation=None, migration=None):
        return dedent(
            f"""

              =======================

              UNSAFE MIGRATION DETCTED:

              - migration: {migration.name}
              - operation: {operation.__class__.__name__}

              Please see the documentation at GITHUB_LINK
            """
        )
