# Django Strong Migrations

Django Strong Migrations was inspired by the wonderful [ankane/strong_migrations](https://github.com/ankane/strong_migrations) for rails.

## Quick start

1. Add "strong_migrations" to your INSTALLED_APPS setting like this::

```
INSTALLED_APPS = [
    ...,
    "strong_migrations",
]
```

### Ignoring Existing Files

Often times users installing this package will have a set of migrations that have already been applied which do not need to be checked for safety.

In order to ignore all of these files, mark a starting point in each of your `apps.py` files, respectively.

```python
# project/apps.py
from django.apps import AppConfig


class MyApp(AppConfig):
    name = "my_app"
    verbose_name = "My App"
    # this will start checking for safety at the next migration, 0174_some_migration
    check_safe_migrations_from = "0173_my_existing_migration"

    def ready(self):
        super().ready()

        import my_app.signals
```

## Unsafe Migrations

### RenameField

Renaming a column that's in use will cause application errors in between migrations running and the application deploying, a safer approach is to:

- Create a new column
- Write to both columns
- Backfill data from the old column to the new column
- Move reads from the old column to the new column
- Stop writing to the old column
- Drop the old column

### RemoveField

Removing a field using the standard `RemoveField` operation result in errors in your migration.

This happens when migrations run before your application has been deployed. Your application will continue referring to the field until it has succesfully been deployed.

The safe migration path is to use a state operation to tell django to ignore the field, deploy that change, and then safely drop the django column afterwards:

```python
# first migration
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('api', 'prior_migration'),
    ]

    operations = [
        migrations.RunSQL(
            sql=migrations.RunSQL.noop,
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[
                migrations.RemoveField(
                    model_name='user',
                    name='my_field',
                )
            ]
        )
    ]
```

deploy the app after the above migration

```python
# subsequent migration
dependencies = [
    ('api', 'first_migration'),
]

operations = [
    migrations.RunSQL(
        sql="alter table user drop column my_field;",
        reverse_sql=migrations.RunSQL.noop
    )
]
```

### Marking Migrations as Safe

you can ignore the error and run the migration anyways by setting `safety_assured=True` in your migration like so:

```python
# unsafe migration
class Migration(migrations.Migration):

    safety_assured = True

    dependencies = [
        ('api', 'prior_migration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='my_field',
        )
    ]
```
