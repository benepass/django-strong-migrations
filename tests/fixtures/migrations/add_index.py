from django.db import migrations, models


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "add_index"

    dependencies = [
        ("testapp", "0002_add_email"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email"], name="email_index"),
        ),
    ]
