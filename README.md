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

## DMS/ Redshift Replication Configuration

You can configure the entire project to check for DMS/Redshift Replication safety:

```python
# settings.py

STRONG_MIGRATIONS_CHECK_DMS_REDSHIFT_SAFETY = True
```

This setting can optionally be set/overridden on an app basis in app settings:

```python
# apps.py
class MyApp(AppConfig):
    name = "my_app"
    verbose_name = "My App"
    check_dms_safety = True

    def ready(self):
        super().ready()

        import my_app.signals
```

Finally, this can be set on a per-model basis like so:

```python
from django.models import Model
class MyModel(Model):
    CHECK_DMS_REDSHIFT_SAFETY = False
```

This is priotized from highest to lowest as:

1. model settings
2. app settings
3. project settings

defaulting to False is none are set.

## Forcing Migrations Through

In a pinch you can use the flag `--skip-strong-migrations` to skip safety checks, but these checks will still be run in your test env until you resolve the issue or mark the migration as safe.

## Unsafe Migrations

Potentially dangerous operations:

- [adding a non-nullable field](#addfield)
- [renaming a field](#renamefield)
- [removing a field](#removefield)

Postgres-specific checks:

- [adding a constraint](#addconstraint)
- [adding an index](#addindex)
- [removing an index](#removeindex)
- [adding a foreign key](#addfield-with-foreignkey)

DMS / Redshift replication specific checks:

- [changing field nullability](#making-field-nullable)

### AddField

Adding a non-nullable field is not safe, even with a default value.

Django will set the default value at the db level only until the column has been added,
and then it will be removed and exist only in the ORM.

The safe migration path is:

1. add the column as nullable with a default value
2. backfill the existing null values
3. make the column not nullable using the safe migration procedure for that.

In Django 5.x you can also use db_default to set a db default safely.

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

Then, in a separate migration, use `VALIDATE CONSTRAINT`, which only takes a `ShareUpdateExclusiveLock` and does not block reads or writes.

```python
from django.db import migrations, models

# first migration: add the constraint without validating existing rows
class Migration(migrations.Migration):
    dependencies = [
        ('app', 'prior_migration'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE "my_model" ADD CONSTRAINT "field_is_positive" CHECK (("field" > 0 OR "field" IS NULL)) NOT VALID;',
            reverse_sql='ALTER TABLE "my_model" DROP CONSTRAINT "field_is_positive"',
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
    ]
```

```python
# second migration: validate the constraint in a separate migration
class Migration(migrations.Migration):
    dependencies = [
        ('app', 'first_migration'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE "my_model" VALIDATE CONSTRAINT "field_is_positive";',
            reverse_sql=migrations.RunSQL.noop,
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

### AddField with ForeignKey

Adding a `ForeignKey` acquires a `ShareRowExclusiveLock` on both the referencing and referenced tables while the constraint is validated against existing rows. This blocks concurrent writes and other FK validations on those tables.

The safe migration path is to decouple the column addition from the constraint validation:

```python
from django.db import migrations, models

# first migration: add the column without a database-level FK constraint
class Migration(migrations.Migration):
    dependencies = [
        ('app', 'prior_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name="my_model",
            name="other_model",
            field=models.ForeignKey(
                to="other_app.OtherModel",
                on_delete=models.SET_NULL,
                null=True,
                db_constraint=False,
            ),
        ),
    ]
```

```python
# second migration: add the FK constraint without validating existing rows
class Migration(migrations.Migration):
    dependencies = [
        ('app', 'first_migration'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE "my_model" ADD CONSTRAINT "my_model_other_model_id_fk" FOREIGN KEY ("other_model_id") REFERENCES "other_app_othermodel" ("id") DEFERRABLE INITIALLY DEFERRED NOT VALID;',
            reverse_sql='ALTER TABLE "my_model" DROP CONSTRAINT "my_model_other_model_id_fk"',
        ),
    ]
```

```python
# third migration: validate the constraint in a separate migration
class Migration(migrations.Migration):
    dependencies = [
        ('app', 'second_migration'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE "my_model" VALIDATE CONSTRAINT "my_model_other_model_id_fk";',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
```

## Redshift / DMS Replication specific checks:

### Making field nullable

Changing the nullability of a column is not supported by redshift.
If this table/column is being copied to Redshift via DMS, setting the field to non-nullable
without setting a db_default value can cause replication failures when null values make their way into that column in redshift.

If you plan on dropping the column:

for django versons >= 5.x: Set a non-null `db_default` value on the field in question.
for django versions < 5.x: Set a non-null column default using a sql migration operation.

** it may be a good idea to set a db_default even if you plan on keeping the column for now, as dropping it in the future will require a db default **

If you plan on maintaining the column:

You will not be able to insert null values in this column in redshift.
If you need null values in this column, you'll need to duplicate and replace the column.

- OR - you could set a transformation rule in DMS.

If you don't need null values, set a db_default on django > 5.x, set a default on django < 5.x.

If you'd like to ignore this table for dms/redshift replication safety,
set
`CHECK_DMS_REDSHIFT_SAFETY=False`
on the model definition.

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
