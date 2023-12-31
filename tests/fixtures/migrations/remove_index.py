from django.db import migrations, models


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "remove_index"

    dependencies = [
        ("testapp", "0002_add_email"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="user",
            name="email_index",
        ),
    ]
