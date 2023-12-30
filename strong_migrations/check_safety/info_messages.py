from textwrap import dedent

INFO_MESSAGES = {
    "pg_alter_field_add_index": dedent(
        """
          Adding an index non-concurrently blocks writes while the index is built.
          Instead, we can use Djangos built in `AddIndexConcurrently`.

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
