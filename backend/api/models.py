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

    YEAR_LEVEL_CHOICE = [
        ("1", "1st Year"),
        ("2", "2nd Year"),
        ("3", "3rd Year"),
        ("4", "4th Year")
    ]

    COURSE_CHOICE = [
        ("BSIT", "Bachelor of Science in Information Technology"),
        ("BSCS", "Bachelor of Science in Computer Science")
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(default='ST', choices=ROLE_CHOICES, max_length=10)
    address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    student_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    course = models.CharField(choices=COURSE_CHOICE, max_length=100, blank=True, null=True)
    year_level = models.CharField(max_length=1, choices=YEAR_LEVEL_CHOICE, blank=True, null=True)
    section = models.CharField(max_length=10, blank=True, null=True)

    department = models.CharField(choices=DEPARTMENT_CHOICE, max_length=10, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    employee_id = models.CharField(max_length=100, blank=True, null=True, unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

def __str__(self):
    return f"{self.first_name} {self.last_name} ({self.get_role_display()})"


class ConsultationSlot(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'IN'})
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_capacity = models.IntegerField(default=1)
    location = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Appointment(models.Model):
    APPOINTMENT_STATUS = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
        ("COMPLETED", "Completed")
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'ST'})
    slot = models.ForeignKey(ConsultationSlot, on_delete=models.CASCADE)
    status = models.CharField(default="PENDING", choices=APPOINTMENT_STATUS, max_length=100)
    reason = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, blank=True, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)