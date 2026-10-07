from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from api.models import ConsultationSlot, ConsultationBooking


User = get_user_model()

class InstructorAttendanceWorkflowTest(APITestCase):
    def setUp(self):
        self.instructor_a = User.objects.create_user(
            role='IN',
            username='ins1',
            email='ins1@test.com'
        )

        self.instructor_b = User.objects.create_user(
            role='IN',
            username='ins2',
            email='ins2@test.com'
        )

        self.student = User.objects.create_user(
            role='ST',
            username='stud',
            email='stud@test.com'
        )

        self.past_slot = ConsultationSlot.objects.create(
            teacher=self.instructor_a,
            date='2026-10-6',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.future_slot = ConsultationSlot.objects.create(
            teacher=self.instructor_a,
            date='2026-10-9',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.other_instructor_slot = ConsultationSlot.objects.create(
            teacher=self.instructor_b,
            date='2026-10-6',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.past_confirmed_booking = ConsultationBooking.objects.create(
            slot=self.past_slot,
            student=self.student,
            status='CONFIRMED',
        )

        self.future_confirmed_booking = ConsultationBooking.objects.create(
            slot=self.future_slot,
            student=self.student,
            status='CONFIRMED',
        )

        self.pending_booking = ConsultationBooking.objects.create(
            slot=self.past_slot,
            student=self.student,
            status='PENDING',
        )

        self.already_completed_booking = ConsultationBooking.objects.create(
            slot=self.past_slot,
            student=self.student,
            status='CONFIRMED',
        )

        self.instructor_b_booking = ConsultationBooking.objects.create(
            slot=self.other_instructor_slot,
            student=self.student,
            status='CONFIRMED',
        )

        self.client = APIClient()

    def test_mark_attendance_completed_success(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-attendance', kwargs={'pk' : self.past_confirmed_booking.pk})
        response = self.client.patch(url, {'status' : 'COMPLETED'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.past_confirmed_booking.refresh_from_db()
        self.assertEqual('COMPLETED', response.data['status'])