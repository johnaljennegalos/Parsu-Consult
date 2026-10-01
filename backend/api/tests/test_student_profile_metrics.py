from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from api.models import ConsultationSlot, ConsultationBooking

User = get_user_model()

class StudentProfileMetricTest(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            role='ST',
            username='stud1',
            email='stud1@test.com'
        )

        self.other_student = User.objects.create_user(
            role='ST',
            username='otherst',
            email='otherst@test.com'
        )

        self.instructor_user = User.objects.create_user(
            role='IN',
            username='ins1',
            email='ins1@test.com'
        )

        self.future_slot = ConsultationSlot.objects.create(
            teacher=self.instructor_user,
            date='2026-10-4',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.past_slot = ConsultationSlot.objects.create(
            teacher=self.instructor_user,
            date='2026-09-26',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.booking1 = ConsultationBooking.objects.create(
            student=self.student_user,
            slot=self.future_slot,
            status='PENDING',
        )

        self.booking2 = ConsultationBooking.objects.create(
            student=self.student_user,
            slot=self.past_slot,
            status='CONFIRMED',
        )

        self.booking3 = ConsultationBooking.objects.create(
            student=self.student_user,
            slot=self.past_slot,
            status='COMPLETED',
        )

        self.booking4 = ConsultationBooking.objects.create(
            student=self.student_user,
            slot=self.past_slot,
            status='NO SHOW',
        )

        self.booking5 = ConsultationBooking.objects.create(
            student=self.student_user,
            slot=self.past_slot,
            status='CANCELLED',
        )

        self.booking6 = ConsultationBooking.objects.create(
            student=self.other_student,
            slot=self.past_slot,
            status='PENDING',
        )

        self.client = APIClient()

    def test_metric_count_assertion(self):
        self.client.force_authenticate(user=self.student_user)

        url = reverse('student-profile-metric')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['metrics']['total_consultations'], 5)
        self.assertEqual(response.data['metrics']['incoming_consultations'], 1)
        self.assertEqual(response.data['metrics']['completed_consultations'], 1)
        self.assertEqual(response.data['metrics']['no_show_consultations'], 1)

    def test_user_isolation(self):
        self.client.force_authenticate(user=self.other_student)

        url = reverse('student-profile-metric')
        response = self.client.get(url)

        self.assertEqual(response.data['metrics']['total_consultations'], 1)

    def test_role_and_permission(self):
        self.client.force_authenticate(user=self.instructor_user)

        url = reverse('student-profile-metric')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=None)
        second_url = reverse('student-profile-metric')
        second_response = self.client.get(second_url)
        self.assertEqual(second_response.status_code, status.HTTP_401_UNAUTHORIZED)

