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

2. If you want to set a lock timeout for your migrations, set

`STRONG_MIGRATIONS_LOCK_TIMEOUT = "2s"` in your `settings.py` file.

Where "2s" is the length of time you want your migration to wait to acquire a lock before failing.

## Ignoring Existing Files

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

## Marking Migrations as Safe

you can skip checks on an operation or operations using the

```python

from strong_migrations import safety_assured

class Migration(migrations.Migration):

    safety_assured = True

    dependencies = [
        ('api', 'prior_migration'),
    ]

    operations = [
        # you can pass in any number of operations
        *safety_assured(
            migrations.RemoveField(
                model_name='user',
                name='my_field',
            )
        ),
        migrations.AddField(...),
    ]
```

## Forcing Migrations Through

In a pinch you can use the flag `--skip-strong-migrations` to skip safety checks, but these checks will still be run in your test env until you resolve the issue or mark the migration as safe.

## Unsafe Migrations

Potentially dangerous operations:

- [renaming a field](#renamefield)
- [removing a field](#removefield)

Postgres-specific checks:

- [adding a constraint](#addconstraint)
- [adding an index](#addindex)
- [removing an index](#removeindex)

### RenameField

Renaming a column that's in use will cause application errors in between migrations running and the application deploying, a safer approach is to:

- Create a new column
- Write to both columns
- Backfill data from the old column to the new column
- Move reads from the old column to the new column
- Stop writing to the old column
- Drop the old column

### RemoveField

Removing a field using the standard `RemoveField` operation can result in errors in your deployment.

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

## Postgres Specific Operations:

### AddConstraint

Adding a constraint will lock the table for reads and writes while the table is scanned in order to validate the constraint.

A safer method is to add the constraint with the `NOT VALID` option, which will add the constraint immediately without validating existing rows.

Then, in a follow up operation, you can use `VALIDATE CONSTRAINT`, which does not updates to the table.

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('app', 'prior_migration'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE "my_model" ADD CONSTRAINT "field_is_positive" CHECK (("field" > 0 OR "field" IS NULL)) NOT VALID;',
            reverse_sql='ALTER TABLE "my_model" DROP CONSTRAINT "field_is_positive"',
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[
                migrations.AddConstraint(
                    model_name="my_model",
                    constraint=models.CheckConstraint(
                        check=models.Q(
                            ("field__gt", 0),
                            ("field__isnull", True),
                            _connector="OR",
                        ),
                        name="field_is_positive",
                    ),
                ),
            ]
        ),
        migrations.RunSQL(
            sql="alter table schedules_schedulelayer validate constraint positive_sl_frequency;",
            reverse_sql=migrations.RunSQL.noop
        )
    ]
```

### AddIndex

Adding an index non-concurrently blocks writes while the index is built. Instead, we can use Djangos built in `AddIndexConcurrently`.

[see pg documentation for more info and caveats](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY)

```python
import django.contrib.postgres.indexes
from django.db import migrations, models
from django.contrib.postgres.operations import AddIndexConcurrently


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("app", "prior_migration"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="my_model",
            index=models.Index(
                fields=["name"], name="name_idx"
            ),
        ),
    ]
```

### RemoveIndex

Removing an index non-concurrently blocks writes while the index is built. Instead, we can use Djangos built in `DropIndexConcurrently`.

[see pg documentation for more info and caveats](https://www.postgresql.org/docs/current/sql-dropindex.html)

```python
import django.contrib.postgres.indexes
from django.db import migrations, models
from django.contrib.postgres.operations import DropIndexConcurrently


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("app", "prior_migration"),
    ]

    operations = [
        DropIndexConcurrently(
            model_name="my_model",
            index=models.Index(
                fields=["name"], name="name_idx"
            ),
        ),
    ]
```

## Contributing

### Tests

- In your python 3.8+ virtualenv, run `pip install -r requirements/test.txt`
- Install your target Django version `pip install Django==4.2`

- In a separate tab, run `docker-compose up` to start the postgres db required for tests.

- `make test`

### Versioning

This package uses the [semver](https://semver.org/) versioning system.

Please make sure to update the version accordingly in `setup.cfg`, and run `python setup.py sdist` to update the version in your PR.

## Credits

authored by @AGarrow
maintained with love by [Benepass](https://www.getbenepass.com/)
