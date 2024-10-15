from textwrap import dedent

INFO_MESSAGES = {
    "add_index": dedent(
        """
          Adding an index non-concurrently blocks writes while the index is built.
          Instead, we can use Djangos built in `AddIndexConcurrently`.
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
                      state_operations=[AlterField(...) or AddIndex(...)]
                  ),
              ]
        """
    ),
    "add_constraint": dedent(
        """
        Adding a constraint will lock the table for reads and writes while the table is
        scanned in order to validate the constraint.

        A safer method is to add the constraint with the `NOT VALID` option, which 
        will add the constraint immediately without validating existing rows.

        Then, in a follow up operation, you can use `VALIDATE CONSTRAINT`, 
        which does not updates to the table.


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
                                ...
                            ),
                            name="some_name",
                        ),
                    ),
                ]
            ),
            migrations.RunSQL(
                sql="alter table schedules_schedulelayer validate constraint positive_sl_frequency;",
                reverse_sql=migrations.RunSQL.noop
            )
        ]
      """
    ),
    "add_non_nullable_field": dedent(
        """
            Adding a non-nullable field is not safe, even with a default value.

            Django will set the default value at the db level only until the column has been added,
            and then it will be removed and exist only in the ORM.

            The safe migration path is:

            1. add the column as nullable with a default value
            2. backfill the existing null values
            3. make the column not nullable using the safe migration procedure for that.

            In Django 5.x you can also use db_default to set a db default safely.
        """
    ),
    "remove_field": dedent(
        """
          Removing a field using the standard `RemoveField` operation can result in errors in your deployment.

          This happens when migrations run before your application has been deployed. Your application will continue referring to the field until it has succesfully been deployed.

          The safe migration path is to use a state operation to tell django to ignore the field, deploy that change, and then safely drop the django column afterwards:

          # first migration

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

          deploy the app after the above migration

          # subsequent migration

          operations = [
              migrations.RunSQL(
                  sql="alter table user drop column my_field;",
                  reverse_sql=migrations.RunSQL.noop
              )
          ]
      """
    ),
    "remove_index": dedent(
        """
      Removing an index non-concurrently blocks writes while the index is built.
      
      Instead, we can use Djangos built in `DropIndexConcurrently`.

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
      """
    ),
    "rename_field": dedent(
        """
          Renaming a column that's in use will cause application errors in between migrations running and the application deploying, a safer approach is to:

          - Create a new column
          - Write to both columns
          - Backfill data from the old column to the new column
          - Move reads from the old column to the new column
          - Stop writing to the old column
          - Drop the old column
    """
    ),
}
