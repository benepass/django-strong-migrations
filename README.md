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

## Unsafe Migrations

### RemoveField

Removing a field using the standard `RemoveField` operation result in errors in your migration. 

This happens when migrations run before your application has been deployed. Your application will continue referring to the field until it has succesfully been deployed.

The safe migration path is to use a state operation to tell django to ignore the field, deploy that change, and then safely drop the django column afterwards:


```python
# first migration
class Migration(migrations.Migration):
    dependencies = [
        ('api', 'prior_migration'),
    ]

    state_operations = [
        migrations.RemoveField(
            model_name='user',
            name='my_field',
        )
    ]
    operations = []
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

