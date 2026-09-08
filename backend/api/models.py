from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = [
        ("ST", "Student"),
        ("IN", "Instructor"),
        ("AD", "Admin")
    ]

    DEPARTMENT_CHOICE = [
        ("IT", "Information Technology"),
        ("CS", "Computer Science")
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(choices=ROLE_CHOICES, max_length=100)
    department = models.CharField(choices=DEPARTMENT_CHOICE, max_length=100)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    student_id = models.CharField(blank=True, null=True)
    employee_id = models.CharField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"