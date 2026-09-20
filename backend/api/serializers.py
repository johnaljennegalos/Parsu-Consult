from rest_framework import serializers
from .models import User, ConsultationSlot, Appointment, Notification
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password


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
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

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
            'student_id' : {'required' : True},
            'course' : {'required' : True},
            'year_level' : {'required' : True},
            'section' : {'required' : True}
        }

    def create(self, validated_data):
        validated_data['role'] = 'ST'
        if 'username' not in validated_data:
            validated_data['username'] = validated_data['email']
        return User.objects.create_user(**validated_data)



class InstructorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

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
            'employee_id' : {'required' : True},
            'department' : {'required' : True}
        }

    def create(self, validated_data):
        validated_data['role'] = 'IN'
        if 'username' not in validated_data:
            validated_data['username'] = validated_data['email']
        return User.objects.create_user(**validated_data)

# The instructor is injected automatically in ViewSet when calling .perform_create(serializer).
#instructor form post/put/patch
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

    def validate(self, attrs):
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError({"end_time": "End time must be strictly after start time."})
        return attrs


#for UI display for both student and insturcotr(GET)
class ConsultationSlotDetailSerializer(serializers.ModelSerializer):
    teacher = UserGeneralSerializer(read_only=True)

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


#for student post/put/patch
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
            'student' : {'read_only' : True},
            'status' : {'read_only' : True}
        }

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        slot = attrs.get('slot', getattr(self.instance, 'slot', None))

        if not slot:
            raise serializers.ValidationError('A valid consultation slot is required')

        if user.role != 'ST':
            raise serializers.ValidationError("Only students can book consultation slots.")

        with transaction.atomic():
            locked_slot = ConsultationSlot.objects.select_for_update().get(id=slot.id)

            if locked_slot.is_deleted or not locked_slot.is_available:
                raise serializers.ValidationError({"slot": "This consultation slot is no longer available."})

            existing_booking = Appointment.objects.filter(
                slot=locked_slot,
                student=user
            ).filter(
                Q(status='PENDING') | Q(status='APPROVED')
            )

            if self.instance:
                existing_booking = existing_booking.exclude(pk=self.instance.pk)

            if existing_booking.exists():
                raise serializers.ValidationError('You already have an active booking')

            if not self.instance:
                active_bookings_count = Appointment.objects.filter(
                    slot=locked_slot
                ).filter(
                    Q(status='PENDING') | Q(status='APPROVED')
                ).count()

                if active_bookings_count >= locked_slot.max_capacity:
                    raise serializers.ValidationError({"slot": "This slot has reached its maximum capacity."})

        return attrs

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


#for student/instructor UI (GET)
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

#both for student and instructors UI, also both for GET or PATCH
class NotificationSerializer(serializers.ModelSerializer):
    appointment = AppointmentDetailSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'appointment',
            'title',
            'message',
            'is_read',
            'created_at'
        ]

        extra_kwargs = {
            'recipient' : {'read_only' : True},
            'title' : {'read_only' : True},
            'message' : {'read_only' : True},
            # 'is_read' : {'read_only' : True}
        }


class ChangePasswordSerializer(serializers.Serializer):
    #data will come from views in json request.data
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Your current password was entered incorrectly')

    def validate_new_password(self, value):
        validate_password(value, user=self.context['request'].user)
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
