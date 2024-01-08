from django.db import migrations


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "rename_field"

    dependencies = [
        ("mock_app", "0002_add_email"),
    ]

    operations = [
        migrations.RenameField(
            model_name="user",
            old_name="email",
            new_name="new_email",
        ),
    ]
