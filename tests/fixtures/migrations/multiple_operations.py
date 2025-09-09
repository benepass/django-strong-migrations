from django.db import migrations, models


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "multiple_operations"

    dependencies = [
        ("testapp", "0002_add_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="alternative_email",
            field=models.CharField(null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="another_email",
            field=models.CharField(null=False),
        ),
    ]
