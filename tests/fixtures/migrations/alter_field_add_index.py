from django.db import migrations, models


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "alter_field_add_index"

    dependencies = [
        ("testapp", "0002_add_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(db_index=True, max_length=254, null=True),
        ),
    ]
