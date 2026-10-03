from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from api.models import ConsultationSlot, ConsultationBooking


User = get_user_model()

class InstructorSlotTest(APITestCase):
    def setUp(self):
        self.instructor_user = User.objects.create_user(
            role='IN',
            username='insuser',
            email='insuser@test.com'
        )

        self.instructor_iso = User.objects.create_user(
            role='IN',
            username='isoins',
            email='isoins@test.com'
        )

        self.student_user = User.objects.create_user(
            role='ST',
            username='stud1',
            email='stud1@test.com'
        )

        self.future_slot = ConsultationSlot.objects.create(
            teacher=self.instructor_user,
            date='2026-10-10',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.client = APIClient()

    def test_create_success(self):
        self.client.force_authenticate(user=self.instructor_user)

        url = reverse('instructor-slot-list-create')
        response = self.client.post(url, {'date' : '2026-10-10', 'start_time' : '14:00:00', 'end_time' : '15:00:00', 'location' : 'Faculty'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        teacher1 = response.data['teacher']
        self.assertTrue(teacher1)

    def test_create_slot_past_date_fails(self):
        self.client.force_authenticate(user=self.instructor_user)

        url = reverse('instructor-slot-list-create')
        response = self.client.post(url, {'date' : '2026-09-01', 'start_time' : '14:00:00', 'end_time' : '15:00:00', 'location' : 'Faculty'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data)

    def test_create_slot_overlap_fails(self):
        self.client.force_authenticate(user=self.instructor_user)

        url = reverse('instructor-slot-list-create')
        response = self.client.post(url, {'date' : '2026-10-10', 'start_time' : '10:30:00', 'end_time' : '11:30:00', 'location' : 'Faculty'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_delete_slot_without_bookings_success(self):
        self.client.force_authenticate(user=self.instructor_user)

        url = reverse('instructor-slot-detail', kwargs={'pk': self.future_slot.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.future_slot.refresh_from_db()
        self.assertTrue(self.future_slot.is_deleted)

    def test_delete_slot_with_active_booking_fails(self):
        self.pending_booking = ConsultationBooking.objects.create(
            student=self.student_user,
            slot=self.future_slot,
            status='PENDING'
        )

        self.client.force_authenticate(user=self.instructor_user)

        url = reverse('instructor-slot-detail', kwargs={'pk': self.future_slot.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.future_slot.refresh_from_db()
        self.assertFalse(self.future_slot.is_deleted)

    def test_student_access_forbidden(self):
        self.client.force_authenticate(user=self.student_user)

        url = reverse('instructor-slot-list-create')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ConsultationSlot.objects.count(), 1)