from getpass import fallback_getpass

from rest_framework import serializers
from .models import User, ConsultationSlot, Appointment, Notification, ConsultationBooking
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from rest_framework.validators import UniqueTogetherValidator
from datetime import datetime


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
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'student_id',
            'course',
            'year_level',
            'section',
            'address',
            'contact_number',
        ]

        extra_kwargs = {
            'student_id': {'required': True},
            'course': {'required': True},
            'year_level': {'required': True},
            'section': {'required': True},
        }

    def create(self, validated_data):
        validated_data['role'] = 'ST'
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **validated_data
        )



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
            'username',
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
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        username = validated_data.pop('username', email)

        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **validated_data
        )

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
            'date',
        ]

        extra_kwargs = {
            'teacher' : {'read_only' : True}
        }

    def validate(self, attrs):
        start = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        date_val = attrs.get('date', getattr(self.instance, 'date', None))
        now = timezone.localtime(timezone.now())

        if date_val < now.date():
            raise serializers.ValidationError({"date": "Cannot create or update a slot in the past."})

        if date_val == now.date() and start < now.time():
            raise serializers.ValidationError({"start_time": "Start time cannot be in the past."})

        if start >= end:
            raise serializers.ValidationError({"end_time": "End time must be strictly after start time."})

        request = self.context.get('request')
        teacher = request.user if request else None

        overlapping_slot = ConsultationSlot.objects.filter(
            teacher=teacher,
            date=date_val,
            is_deleted=False,
            start_time__lt=end,
            end_time__gt=start
        )

        if self.instance is not None:
            overlapping_slot = overlapping_slot.exclude(pk=self.instance.pk)

        if overlapping_slot.exists():
            raise serializers.ValidationError({
                "non_field_errors": ["You already have an overlapping consultation slot for this time range."]
            })

        return attrs


class ConsultationBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationBooking
        fields = '__all__'

        read_only_fields = ['student', 'status', 'created_at']

    def validate(self, attrs):

        if self.instance:
            if self.instance.status == 'CANCELLED':
                raise serializers.ValidationError({'status': 'Booking is already cancelled.'})
            return attrs

        slot = attrs.get('slot')
        if not slot:
            raise serializers.ValidationError({'slot': 'This field is required.'})

        if not slot.is_available or slot.is_deleted:
            raise serializers.ValidationError({'slot' : 'This consultation slot is no longer available.'})

        now = timezone.localtime(timezone.now())
        if slot.date < now.date() or (slot.date == now.date() and slot.start_time <= now.time()):
            raise serializers.ValidationError({"slot": "Cannot book a consultation slot that has already passed."})

        active_count = slot.bookings.exclude(status='CANCELLED').count()
        if active_count >= slot.max_capacity:
            raise serializers.ValidationError({'slot': 'This consultation slot has reached maximum capacity.'})

        user = self.context['request'].user
        # active_booking = slot.bookings.filter(status='CONFIRMED').count()
        has_active_booking = slot.bookings.filter(student=user).exclude(status='CANCELLED').exists()
        if has_active_booking:
            raise serializers.ValidationError({"slot": "You already have an active booking for this slot."})

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
            'date',
        ]

class StudentBookingHistorySerializer(serializers.ModelSerializer):
    slot = ConsultationSlotDetailSerializer(read_only=True)
    is_past_slot = serializers.SerializerMethodField()

    class Meta:
        model = ConsultationBooking
        fields = [
            'id',
            'slot',
            'status',
            'created_at',
            'is_past_slot',
        ]

    def get_is_past_slot(self, obj):
        end_time = datetime.combine(obj.slot.date, obj.slot.end_time)
        aware_end_time = timezone.make_aware(end_time)

        if aware_end_time < timezone.now():
            print('Slot time is in the past')
            return True
        return False


class InstructorRosterSerializer(serializers.ModelSerializer):
    student = UserGeneralSerializer(read_only=True)

    class Meta:
        model = ConsultationBooking
        fields = [
            'id',
            'student',
            'status',
            'created_at'
        ]

class AttendanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationBooking
        fields = [
            'status'
        ]

    def validate(self, attrs):
        status = attrs.get('status')
        state = self.instance.status
        date = self.instance.slot.date
        end_time = self.instance.slot.end_time
        naive_slot_time = datetime.combine(date, end_time)
        aware_slot_time = timezone.make_aware(naive_slot_time)

        if status not in ['COMPLETED', 'NO SHOW']:
            raise serializers.ValidationError({'status' : 'Cannot modify confirmed or cancelled appointment.'})

        if state == 'CANCELLED' or state == 'COMPLETED' or state == 'NO SHOW':
            raise serializers.ValidationError({'status' : 'Cannot modify finalized appointment'})

        if aware_slot_time > timezone.now():
            raise serializers.ValidationError({'status' : 'Cannot mark attendance for a future consultation slot.'})

        return attrs




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

        if not user or not user.is_authenticated:
            raise serializers.ValidationError({'non_field_errors' : ['User must be authenticated']})

        if not user.check_password(value):
            raise serializers.ValidationError('Your current password was entered incorrectly')

        return value

    def validate_new_password(self, value):
        user = self.context['request'].user
        user_obj = user if user and user.is_authenticated else None
        validate_password(value, user=user_obj)
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

class StudentLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)


    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

            if not user:
                raise serializers.ValidationError({'error' : 'Unable to login with provided credentials'})

            if getattr(user, 'role', None) != 'ST':
                raise serializers.ValidationError({'error' : 'Only user with ST role are allowed'})

        else:
            raise serializers.ValidationError({'error' : 'Must include both username and password'})

        attrs['user'] = user
        return attrs


class InstructorLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

            if not user:
                raise AuthenticationFailed('Unable to login with provided credentials')

            if getattr(user, 'role', None) != 'IN':
                raise AuthenticationFailed('Only user with IN role are allowed')

        else:
            raise serializers.ValidationError({'error' : 'Must include both username and password'})

        attrs['user'] = user
        return attrs


class InstructorPublicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'contact_number',
            'department',
            'specialization',
        ]
        
        
        
class StudentProfileMetricsSerializer(serializers.ModelSerializer):
    student = UserGeneralSerializer(source='*', read_only=True)
    metrics = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'student',
            'metrics'
        ]

    def get_metrics(self, obj):
        fallback_metrics = {
            'total_consultations': 0,
            'incoming_consultations': 0,
            'completed_consultations': 0,
            'no_show_consultations': 0
        }

        metrics_data = self.context.get(
            'metrics', fallback_metrics
        )

        return metrics_data

