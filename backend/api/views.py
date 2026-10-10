from gc import get_objects
from logging import raiseExceptions

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta


from .serializers import StudentLoginSerializer, StudentRegistrationSerializer, InstructorLoginSerializer, InstructorRegistrationSerializer, InstructorPublicProfileSerializer, ConsultationSlotSerializer, ConsultationBookingSerializer, ConsultationSlotDetailSerializer, StudentBookingHistorySerializer, InstructorRosterSerializer, AttendanceUpdateSerializer, StudentProfileMetricsSerializer, InstructorBookingDetailSerializer, InstructorBookingDecisionSerializer, InstructorAttendanceSerializer, InstructorAnalyticsSerializer

from .permissions import IsStudent, IsInstructor
from .models import User, ConsultationSlot, ConsultationBooking


class StudentLoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = StudentLoginSerializer(data=request.data, context={'request' : request})

        if not serializer.is_valid():
            if 'password' in serializer.errors or 'username' in serializer.errors:
                return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role' : user.role
        }, status=status.HTTP_200_OK)


class StudentRegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InstructorLoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InstructorLoginSerializer(data=request.data, context={'request' : request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']

        if user is None:
            return Response({'errors' : 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.role != 'IN':
            return Response({'error' : 'Account is not registered as Instructor'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role' : user.role
        }, status=status.HTTP_200_OK)


class InstructorRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InstructorRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


User = get_user_model()

class InstructorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = InstructorPublicProfileSerializer

    def get_queryset(self):
        queryset = User.objects.filter(role='IN')

        search_queryset = self.request.query_params.get('search', '').strip()

        if search_queryset:
            queryset = queryset.filter(
                Q(first_name__icontains=search_queryset) |
                Q(last_name__icontains=search_queryset) |
                Q(department__icontains=search_queryset) |
                Q(specialization__icontains=search_queryset)
            )
        else:
            student_dept = self.request.user.department

            if student_dept:
                queryset = queryset.filter(department=student_dept)
            else:
                return User.objects.none()

        return queryset


class InstructorDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = InstructorPublicProfileSerializer
    queryset = User.objects.filter(role='IN')


class ConsultationSlotListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = ConsultationSlotSerializer

    def get_queryset(self):
        return ConsultationSlot.objects.filter(teacher=self.request.user, is_deleted=False)


    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class ConsultationSlotDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = ConsultationSlotSerializer

    def get_queryset(self):
        return ConsultationSlot.objects.filter(teacher=self.request.user, is_deleted=False)

    def perform_destroy(self, instance):
        instance.soft_delete()

class AvailableSlotListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = ConsultationSlotDetailSerializer

    def get_queryset(self):
        queryset = ConsultationSlot.objects.filter(is_available=True, is_deleted=False, date__gte=timezone.localtime(timezone.now()).date())

        teacher_id = self.request.query_params.get('teacher_id')

        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        return queryset


class ConsultationBookingListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = ConsultationBookingSerializer

    def get_queryset(self):
        return ConsultationBooking.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

class ConsultationBookingCancelView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = ConsultationBookingSerializer

    def get_queryset(self):
        return ConsultationBooking.objects.filter(student=self.request.user, status__in=['PENDING', 'CONFIRMED'])

    def perform_update(self, serializer):
        serializer.save(status='CANCELLED')


class StudentBookingHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = StudentBookingHistorySerializer

    def get_queryset(self):
        return ConsultationBooking.objects.filter(student=self.request.user)


class InstructorRosterView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = InstructorRosterSerializer

    def get_queryset(self):
        return ConsultationBooking.objects.filter(slot__teacher=self.request.user)


class AttendanceUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = AttendanceUpdateSerializer
    
    http_method_names = ['patch', 'put']

    def get_queryset(self):
        return ConsultationBooking.objects.filter(slot__teacher=self.request.user)
    

class StudentProfileMetricView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        today = timezone.localtime(timezone.now()).date()

        metrics_data = ConsultationBooking.objects.filter(
            student=request.user
        ).aggregate(
            total_consultations=Count('id'),
            incoming_consultations=Count('id', filter=Q(status__in=['PENDING', 'CONFIRMED'], slot__date__gte=today)),
            completed_consultations=Count('id', filter=Q(status='COMPLETED')),
            no_show_consultations=Count('id', filter=Q(status='NO SHOW'))
        )

        serializers = StudentProfileMetricsSerializer(request.user, context={'request' : request, 'metrics' : metrics_data})

        return Response(serializers.data, status=status.HTTP_200_OK)

#GET and POST
class InstructorSlotListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = ConsultationSlotSerializer

    def get_queryset(self):
        return ConsultationSlot.objects.filter(teacher=self.request.user, is_deleted=False).order_by('date', 'start_time')

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


#GET PATCH DELETE
class InstructorSlotDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = ConsultationSlotSerializer

    def get_queryset(self):
        return ConsultationSlot.objects.filter(teacher=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        has_active_booking = ConsultationBooking.objects.filter(status__in=['PENDING', 'CONFIRMED'], slot=instance)

        if has_active_booking.exists():
            return Response({"detail": "Cannot delete or cancel a slot that has active student bookings."},
                            status=status.HTTP_400_BAD_REQUEST
                            )
        instance.is_deleted = True
        instance.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class InstructorBookingListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = InstructorBookingDetailSerializer

    def get_queryset(self):
        queryset = ConsultationBooking.objects.filter(slot__teacher=self.request.user, slot__is_deleted=False).select_related('slot', 'student')

        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())

        return queryset.order_by('-created_at')


class InstructorBookingDecisionView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = InstructorBookingDecisionSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return ConsultationBooking.objects.filter(slot__teacher=self.request.user, slot__is_deleted=False, status='PENDING').select_related('slot')


class InstructorBookingAttendanceView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = InstructorAttendanceSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return ConsultationBooking.objects.filter(slot__teacher=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InstructorAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsInstructor]
    serializer_class = InstructorAnalyticsSerializer

    def get(self, request):
        user = request.user
        now = timezone.now()
        current_date = now.date()
        current_time = now.time()

        base_query = ConsultationBooking.objects.filter(slot__teacher=user)

        metrics = base_query.aggregate(
            total_consultations=Count('id'),
            completed_consultations=Count('id', filter=Q(status='COMPLETED')),
            no_show_consultations=Count('id', filter=Q(status='NO SHOW')),
            cancelled_consultations=Count('id', filter=Q(status__in=['CANCELLED', 'REJECTED'])),
            upcoming_confirmed_count=Count(
                'id',
                filter=Q(status='CONFIRMED') & (
                    Q(slot__date__gt=current_date) |
                    Q(slot__date=current_date, slot__start_time__gt=current_time)
                )
            )
        )

        completed_consultations = base_query.filter(status='COMPLETED').select_related('slot')

        total_seconds = 0.00

        for bookings in completed_consultations:
            slot_date = bookings.slot.date
            start_time = bookings.slot.start_time
            end_time = bookings.slot.end_time

            start_datetime = datetime.combine(slot_date, start_time)
            end_datetime = datetime.combine(slot_date, end_time)

            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)

            duration = end_datetime - start_datetime

            total_seconds += duration.total_seconds()

        final_hours = round(total_seconds / 3600.0, 2)

        total_consultations = metrics['completed_consultations'] + metrics['no_show_consultations']

        if total_consultations > 0:
            rate = round((metrics['completed_consultations'] / total_consultations) * 100.0, 2)
        else:
            rate = 0.00

        analytics_payload = {
            'total_consultations': metrics['total_consultations'],
            'completed_consultations': metrics['completed_consultations'],
            'no_show_consultations': metrics['no_show_consultations'],
            'cancelled_consultations': metrics['cancelled_consultations'],
            'upcoming_confirmed_count': metrics['upcoming_confirmed_count'],
            'completion_rate': rate,
            'total_hours_consulted': final_hours,
        }

        serializers = InstructorAnalyticsSerializer(data=analytics_payload)
        serializers.is_valid(raise_exception=True)
        return Response(serializers.data, status=status.HTTP_200_OK)




