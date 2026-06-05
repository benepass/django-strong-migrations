from django.db import migrations, models


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "add_nullable_foreign_key_no_db_constraint"

    dependencies = [
        ("testapp", "0002_add_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="related_user",
            field=models.ForeignKey(
                to="mock_app.user",
                on_delete=models.SET_NULL,
                null=True,
                db_constraint=False,
            ),
        ),
    ]
