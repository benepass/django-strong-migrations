from django.db import models


# Create your models here.
class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(null=True, db_index=True)
