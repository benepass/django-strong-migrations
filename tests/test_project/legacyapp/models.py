from django.db import models


# Create your models here.
class LegacyModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    renamed_test_field = models.CharField(max_length=15)
