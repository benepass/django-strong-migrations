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
                  state_operations=[AlterField(...)]
              ),
          ]
        """
    ),
}
