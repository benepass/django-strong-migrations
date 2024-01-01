from django.db.migrations.operations.base import Operation


def safety_assured(*operations: Operation) -> list[Operation]:
    """
    accepts operations as arguments, returns a list of operations marked safe
    """
    safe_operations = []
    for operation in operations:
        setattr(operation, "safety_assured", True)
        safe_operations.append(operation)
    return safe_operations
