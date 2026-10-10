from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from api.models import ConsultationSlot, ConsultationBooking


User = get_user_model()

class InstructorAnalyticsTest(APITestCase):
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

        self.url = reverse('instructor-analytics')

        self.past_slot1 = ConsultationSlot.objects.create(
            teacher=self.instructor_a,
            date='2026-10-6',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.past_slot2 = ConsultationSlot.objects.create(
            teacher=self.instructor_a,
            date='2026-10-06',
            start_time='14:00:00',
            end_time='15:00:00',
            location='Faculty Room',
            max_capacity=3,
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

        self.completed_booking1 = ConsultationBooking.objects.create(
            slot=self.past_slot1,
            student=self.student,
            status='COMPLETED',
        )

        self.completed_booking2 = ConsultationBooking.objects.create(
            slot=self.past_slot2,
            student=self.student,
            status='COMPLETED',
        )

        self.no_show_booking = ConsultationBooking.objects.create(
            slot=self.past_slot2,
            student=self.student,
            status='NO SHOW',
        )

        self.cancelled_booking = ConsultationBooking.objects.create(
            slot=self.past_slot2,
            student=self.student,
            status='CANCELLED',
        )

        self.upcoming_confirmed_booking = ConsultationBooking.objects.create(
            slot=self.future_slot,
            student=self.student,
            status='CONFIRMED',
        )

        self.client = APIClient()

    def test_analytics_metrics_calculation_accuracy(self):
        self.client.force_authenticate(user=self.instructor_a)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_consultations'], 5)
        self.assertEqual(response.data['completed_consultations'], 2)
        self.assertEqual(response.data['no_show_consultations'], 1)
        self.assertEqual(response.data['cancelled_consultations'], 1)
        self.assertEqual(response.data['upcoming_confirmed_count'], 1)
        self.assertEqual(response.data['completion_rate'], 66.67)
        self.assertEqual(response.data['total_hours_consulted'], 2.0)

    def test_zero_division_safety_for_new_instructor(self):
        self.client.force_authenticate(self.instructor_b)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['completion_rate'], 0.0)
        self.assertEqual(response.data['total_hours_consulted'], 0.0)
        self.assertEqual(response.data['total_consultations'], 0)

    def test_tenant_isolation_and_permissions(self):
        self.client.force_authenticate(self.instructor_b)
        response = self.client.get(self.url)
        self.assertEqual(response.data['total_consultations'], 0)

        self.client.force_authenticate(self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
