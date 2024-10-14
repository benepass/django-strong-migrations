from django.db import migrations, models


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "remove_field"

    dependencies = [
        ("testapp", "0002_add_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="alternative_email",
            field=models.EmailField(
                default="my_alternative_email@megacorp.com", null=True
            ),
        ),
    ]
