from django.db import migrations, models


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "add_index"

    dependencies = [
        ("testapp", "0002_add_email"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_null=False),
                fields=("email"),
                name="unique_email_if_not_null",
            ),
        ),
    ]
