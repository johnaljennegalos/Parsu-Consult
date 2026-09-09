from django.contrib import admin
from .models import User, Student, Instructor, ConsultationSlot, Appointment

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


@admin.register(ConsultationSlot)
class ConsultationSlotAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'date', 'start_time', 'end_time', 'max_capacity', 'location', 'is_available', 'created_at']
    list_filter = ['is_available', 'date', 'teacher']
    search_fields = ['teacher__email', 'teacher__first_name', 'teacher__last_name']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'slot', 'status', 'reason', 'rejection_reason', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'slot__teacher']
    search_fields = ['student__first_name', 'student__last_name', 'slot__teacher__first_name']

    @admin.display(description="Instructor")
    def get_teacher(self, obj):
        return obj.slot.teacher
