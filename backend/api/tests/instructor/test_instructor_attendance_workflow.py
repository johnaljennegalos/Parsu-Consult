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
            date='2026-10-15',
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
            status='COMPLETED',
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

    def test_mark_attendance_no_show_success(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-attendance', kwargs={'pk' : self.past_confirmed_booking.pk})
        response = self.client.patch(url, {'status' : 'NO SHOW'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.past_confirmed_booking.refresh_from_db()
        self.assertEqual('NO SHOW', response.data['status'])

    def test_mark_attendance_future_slot_fails(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-attendance', kwargs={'pk' : self.future_confirmed_booking.pk})
        response = self.client.patch(url, {'status': 'COMPLETED'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.future_confirmed_booking.refresh_from_db()
        self.assertEqual(self.future_confirmed_booking.status, 'CONFIRMED')

    def test_mark_attendance_on_pending_booking_fails(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-attendance', kwargs={'pk' : self.pending_booking.pk})
        response = self.client.patch(url, {'status': 'COMPLETED'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.pending_booking.refresh_from_db()
        self.assertIn('status', response.data)

    def test_mark_attendance_terminal_state_immutable(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-attendance', kwargs={'pk' : self.already_completed_booking.pk})
        response = self.client.patch(url, {'status': 'NO SHOW'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.already_completed_booking.refresh_from_db()
        self.assertEqual(self.already_completed_booking.status, 'COMPLETED')

    def test_cross_instructor_attendance_returns_404(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-attendance', kwargs={'pk' : self.instructor_b_booking.pk})
        response = self.client.patch(url, {'status': 'COMPLETED'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.instructor_b_booking.refresh_from_db()
        self.assertEqual(self.instructor_b_booking.status, 'CONFIRMED')

    def test_student_role_forbidden(self):
        self.client.force_authenticate(self.student)

        url = reverse('instructor-booking-attendance', kwargs={'pk' : self.past_confirmed_booking.pk})
        response = self.client.patch(url, {'status': 'COMPLETED'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_unauthorized(self):
        self.client.logout()

        url = reverse('instructor-booking-attendance', kwargs={'pk' : self.past_confirmed_booking.pk})
        response = self.client.patch(url, {'status': 'COMPLETED'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
