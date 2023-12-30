from django.db import migrations


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "remove_field"

    dependencies = [
        ("testapp", "0002_add_email"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="email",
        ),
    ]
