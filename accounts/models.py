from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):

    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('worker', 'Worker'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    age = models.IntegerField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    auto_location = models.CharField(max_length=255, blank=True, null=True)
    points = models.IntegerField(default=0)
    badge = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.username
