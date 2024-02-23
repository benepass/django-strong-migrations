from .mock_cursor_wrapper import MockCursorWrapper


class MockConnection:
    def cursor(self):
        return MockCursorWrapper()
