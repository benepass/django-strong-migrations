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

        Then, in a separate migration, use `VALIDATE CONSTRAINT`, which only takes a
        ShareUpdateExclusiveLock and does not block reads or writes.

        # first migration: add the constraint without validating existing rows
        operations = [
            migrations.RunSQL(
                sql='ALTER TABLE "my_model" ADD CONSTRAINT "field_is_positive" CHECK (("field" > 0 OR "field" IS NULL)) NOT VALID;',
                reverse_sql='ALTER TABLE "my_model" DROP CONSTRAINT "field_is_positive"',
                state_operations=[
                    migrations.AddConstraint(
                        model_name="my_model",
                        constraint=models.CheckConstraint(
                            check=models.Q(
                                ...
                            ),
                            name="field_is_positive",
                        ),
                    ),
                ]
            ),
        ]

        # second migration: validate the constraint in a separate migration
        operations = [
            migrations.RunSQL(
                sql='ALTER TABLE "my_model" VALIDATE CONSTRAINT "field_is_positive";',
                reverse_sql=migrations.RunSQL.noop,
            )
        ]
      """
    ),
    "add_foreign_key": dedent(
        """
        Adding a ForeignKey acquires a ShareRowExclusiveLock on both the referencing
        and referenced tables while the constraint is validated against existing rows.
        This blocks concurrent writes and other FK validations on those tables.

        The safe migration path is to add the column with db_constraint=False and
        the FK constraint NOT VALID in one migration, then validate in a separate
        migration. VALIDATE CONSTRAINT must be in its own migration so the
        AccessExclusiveLock is released before the (non-blocking) validation scan runs.

        # first migration: add the column and the NOT VALID FK constraint
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
            migrations.RunSQL(
                sql='ALTER TABLE "my_model" ADD CONSTRAINT "my_model_other_model_id_fk" FOREIGN KEY ("other_model_id") REFERENCES "other_app_othermodel" ("id") DEFERRABLE INITIALLY DEFERRED NOT VALID;',
                reverse_sql='ALTER TABLE "my_model" DROP CONSTRAINT "my_model_other_model_id_fk"',
            ),
        ]

        # second migration: validate the constraint in a separate migration
        operations = [
            migrations.RunSQL(
                sql='ALTER TABLE "my_model" VALIDATE CONSTRAINT "my_model_other_model_id_fk";',
                reverse_sql=migrations.RunSQL.noop,
            ),
        ]
      """
    ),
    "alter_field_make_nullable_dms_redshift": dedent(
        """
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
            CHECK_DMS_REDSHIFT_SAFETY=False
            on the model definition.
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
