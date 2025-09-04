from django.db import migrations, models


class Migration(migrations.Migration):
    app_label = "mock_app"
    name = "remove_field"

    dependencies = [
        ("testapp", "0002_add_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userwithdmsredshiftdisabled",
            name="non_null_field_without_default",
            field=models.CharField(null=True),
        ),
    ]
