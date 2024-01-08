from django.db import migrations, models

from strong_migrations import safety_assured


def test_safety_assured_with_one_operation():
    operations = safety_assured(
        migrations.AddField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, null=True),
        )
    )
    assert len(operations) == 1
    assert operations[0].safety_assured is True
    assert isinstance(operations[0], migrations.AddField)


def test_safety_assured_with_multiple_operations():
    operations = safety_assured(
        migrations.AddField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, null=True),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email"], name="email_index"),
        ),
    )
    assert len(operations) == 2
    assert operations[0].safety_assured is True
    assert isinstance(operations[0], migrations.AddField)

    assert operations[1].safety_assured is True
    assert isinstance(operations[1], migrations.AddIndex)
