from django.db import models
from django.conf import settings
import uuid


class Complaint(models.Model):

    # -----------------------------
    # STATUS OPTIONS
    # -----------------------------
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('in_progress', 'In Progress'),
        ('cleaned', 'Cleaned'),
        ('rejected', 'Rejected'),
    )

    # -----------------------------
    # GARBAGE SIZE OPTIONS
    # -----------------------------
    SIZE_CHOICES = (
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    )

    # -----------------------------
    # AREA TYPE (Public / Private)
    # -----------------------------
    AREA_CHOICES = (
        ('public', 'Public Area'),
        ('private', 'Private Area'),
    )

    # -----------------------------
    # SEVERITY LEVEL (Optional)
    # -----------------------------
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )

    # -----------------------------
    # MAIN FIELDS
    # -----------------------------

    complaint_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints"
    )

    image = models.ImageField(upload_to='complaints/')

    latitude = models.FloatField()
    longitude = models.FloatField()

    area_type = models.CharField(
        max_length=20,
        choices=AREA_CHOICES,
        default='public'
    )

    size_category = models.CharField(
        max_length=20,
        choices=SIZE_CHOICES,
        blank=True,
        null=True
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    cleaned_at = models.DateTimeField(blank=True, null=True)
    cleaned_image = models.ImageField(upload_to='cleaned_proofs/', blank=True, null=True)
    location_name = models.TextField(blank=True, null=True)

    # -----------------------------
    # META CONFIG
    # -----------------------------
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.complaint_id} - {self.status}"

class SystemSettings(models.Model):
    AREA_VISIBILITY_CHOICES = (
        ('public', 'Public Area Only'),
        ('private', 'Private Area Only'),
        ('both', 'Both Public and Private'),
    )

    visible_area = models.CharField(
        max_length=20,
        choices=AREA_VISIBILITY_CHOICES,
        default='both'
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return f"Visibility: {self.get_visible_area_display()}"

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(id=1)
        return settings

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('verified', 'Complaint Accepted'),
        ('in_progress', 'Cleaning in Progress'),
        ('cleaned', 'Cleanup Completed'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE
    )
    message = models.TextField()
    status_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.status_type}"
