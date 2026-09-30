from datetime import timedelta, time
from django.utils import timezone
from http.client import responses

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from api.models import ConsultationSlot, ConsultationBooking

User = get_user_model()

class StudentLifecycleTest(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            role='IN',
            username='ins1',
            email='ins1@test.com'
        )

        self.student1 = User.objects.create_user(
            role='ST',
            username='stud1',
            email='stud1@test.com'
        )

        self.student2 = User.objects.create_user(
            role='ST',
            username='stud2',
            email='stud2@test.com'
        )

        self.past_slot = ConsultationSlot.objects.create(
            teacher=self.instructor,
            date=timezone.now().date() - timedelta(days=1),
            start_time=time(9, 0),
            end_time=time(10, 0),
            max_capacity=5
        )

        self.future_slot = ConsultationSlot.objects.create(
            teacher=self.instructor,
            date=timezone.now().date() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(11, 0),
            max_capacity=5
        )

        self.past_booking = ConsultationBooking.objects.create(
            slot=self.past_slot,
            student=self.student1,
            status='CONFIRMED'
        )

        self.future_booking = ConsultationBooking.objects.create(
            slot=self.future_slot,
            student=self.student1,
            status='CONFIRMED'
        )

        self.student_2_booking = ConsultationBooking.objects.create(
            slot=self.past_slot,
            student=self.student2,
            status='CONFIRMED'
        )

        self.client = APIClient()

    def test_student_can_fetch_own_history(self):
        self.client.force_authenticate(user=self.student1)

        url = reverse('student-booking-history')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        bookings_by_id = {item['id']: item for item in response.data}

        past_booking = bookings_by_id[self.past_booking.id]
        self.assertTrue(past_booking['is_past_slot'])

        future_booking = bookings_by_id[self.future_booking.id]
        self.assertFalse(future_booking['is_past_slot'])

    def test_cannot_mark_future_booking_completed(self):
        self.client.force_authenticate(user=self.instructor)

        url = reverse('attendance-update', kwargs={'pk' : self.future_booking.id})
        response = self.client.patch(url, {'status': 'COMPLETED'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.future_booking.refresh_from_db()
        self.assertEqual(self.future_booking.status, 'CONFIRMED')

    def test_cannot_update_already_finalized_booking(self):
        self.past_booking.status = 'COMPLETED'
        self.past_booking.save()

        self.client.force_authenticate(user=self.instructor)

        url = reverse('attendance-update', kwargs={'pk' : self.past_booking.id})
        response = self.client.patch(url, {'status': 'NO SHOW'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_update_attendance(self):
        self.client.force_authenticate(user=self.student1)

        url = reverse('attendance-update', kwargs={'pk' : self.past_booking.id})
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_instructor_can_mark_past_booking_completed(self):
        self.client.force_authenticate(user=self.instructor)

        url = reverse('attendance-update', kwargs={'pk': self.past_booking.id})
        response = self.client.patch(url, {'status' : 'COMPLETED'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.past_booking.refresh_from_db()
        self.assertEqual(self.past_booking.status, 'COMPLETED')

    def test_student_cannot_see_other_students_bookings(self):
        self.client.force_authenticate(user=self.student1)

        url = reverse('student-booking-history')
        response = self.client.get(url)

        returned_id = {item['id']: item for item in response.data}

        self.assertNotIn(self.student_2_booking.id, returned_id)

    def test_instructor_can_view_roster(self):
        self.client.force_authenticate(user=self.instructor)

        url = reverse('instructor-roster')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        first_booking = response.data[0]
        self.assertTrue('student', first_booking)
        self.assertTrue('username', first_booking['student'])
