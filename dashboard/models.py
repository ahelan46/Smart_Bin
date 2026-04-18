# In your accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # ... your other fields ...
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_groups', # Unique name
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions', # Unique name
        blank=True
    )