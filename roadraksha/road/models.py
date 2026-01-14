from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid  



# Create your models here.

class AdminUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username


class AuthorityProfile(models.Model):

    AUTHORITY_CHOICES = [
        ('ROAD', 'Road Authority'),
        ('WATER', 'Water Authority'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    authority_type = models.CharField(
        max_length=10,
        choices=AUTHORITY_CHOICES
    )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    #created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.authority_type}"
    


class Report(models.Model):

    REPORT_TYPES = [
        ('ROAD', 'road'),
        ('WATER', 'water'),
    ]

    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    report_type = models.CharField(max_length=5, choices=REPORT_TYPES)

    description = models.TextField()

    status = models.BooleanField(default=False)  # False = Open, True = Closed (by authorities)
    admin_verified = models.BooleanField(default=False) #for admin verification of report
    reported_at = models.DateTimeField(auto_now_add=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)

    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"{self.report_type} | {self.report_id} | {'Closed' if self.status else 'Open'}"
