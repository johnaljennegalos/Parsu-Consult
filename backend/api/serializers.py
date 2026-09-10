from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import User, ConsultationSlot, Appointment


class UserGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'role',
            'address',
            'contact_number',
            'first_name',
            'last_name',
            'student_id',
            'course',
            'year_level',
            'section',
            'department',
            'specialization',
            'employee_id',
        ]

        extra_kwargs = {
            'role' : {'read_only' : True},
            'student_id' : {'read_only' : True},
            'employee_id' : {'read_only' : True}
        }


class StudentRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'student_id',
            'first_name',
            'last_name',
            'email',
            'password',
            'contact_number',
            'address',
            'course',
            'year_level',
            'section'
        ]

        extra_kwargs = {
            'password' : {'write_only' : True},
            'student_id' : {'required' : True},
            'course' : {'required' : True},
            'year_level' : {'required' : True},
            'section' : {'required' : True}
        }

    def create(self, validated_data):
        validated_data['role'] = 'ST'
        user = User.objects.create_user(**validated_data)
        return user


class InstructorRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'employee_id',
            'first_name',
            'last_name',
            'email',
            'password',
            'contact_number',
            'address',
            'department',
            'specialization'
        ]

        extra_kwargs = {
            'password' : {'write_only' : True},
            'employee_id' : {'required' : True},
            'department' : {'required' : True}
        }

    def create(self, validated_data):
        validated_data['role'] = 'IN'
        user = User.objects.create_user(**validated_data)
        return user

# The instructor is injected automatically in ViewSet when calling .perform_create(serializer).
class ConsultationSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationSlot
        fields = [
            'id',
            'teacher',
            'start_time',
            'end_time',
            'max_capacity',
            'location',
        ]

        extra_kwargs = {
            'teacher' : {'read_only' : True}
        }


class ConsultationSlotDetailSerializer(serializers.ModelSerializer):
    teacher = UserGeneralSerializer(read_only=True)

    class Meta:
        model = ConsultationSlot
        fields = [
            'id',
            'employee_id',
            'first_name',
            'last_name',
            'department'
        ]



class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'id',
            'student',
            'slot',
            'status',
            'reason',
        ]

        extra_kwargs = {
            'student' : {'read_only' : True}
        }

class AppointmentDetailSerializer(serializers.ModelSerializer):
    student = UserGeneralSerializer(read_only=True)

    slot = ConsultationSlotDetailSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id',
            'student',
            'slot',
            'status',
            'reason',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]
