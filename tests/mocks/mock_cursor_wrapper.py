class MockCursorWrapper:
    def execute(self, *args, **kwargs):
        return True

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        return self
