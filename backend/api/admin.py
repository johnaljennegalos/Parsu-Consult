from django.contrib import admin
from .models import User, Student, Instructor

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['role', 'first_name', 'last_name', 'email', 'address', 'contact_number']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'first_name', 'last_name', 'email', 'course', 'year_level', 'section', 'contact_number']
    list_filter = ['course', 'year_level', 'section']
    search_fields = ['student_id', 'first_name', 'last_name', 'email']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='ST')

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'first_name', 'last_name', 'email', 'contact_number', 'specialization', 'department']
    list_filter = ['department', 'specialization', 'employee_id']
    search_fields = ['employee_id', 'first_name', 'last_name', 'department']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='IN')
