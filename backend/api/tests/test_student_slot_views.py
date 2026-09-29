from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from api.models import ConsultationSlot

User = get_user_model()

class StudentSlotAPITest(APITestCase):
    def setUp(self):
        self.student_1 = User.objects.create_user(
            role='ST',
            username='stud1',
            email='stud1@test.com'
        )

        self.instructor_1 = User.objects.create_user(
            role='IN',
            username='ins1',
            email='ins1@test.com'
        )

        self.instructor_2 = User.objects.create_user(
            role='IN',
            username='ins2',
            email='ins2@test.com'
        )

        self.slot_a = ConsultationSlot.objects.create(
            teacher=self.instructor_1,
            date='2026-09-29',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Room 101',
            max_capacity=2,
            is_available=True,
            is_deleted=False
        )

        self.slot_b = ConsultationSlot.objects.create(
            teacher=self.instructor_1,
            date='2026-09-29',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Room 101',
            max_capacity=2,
            is_available=True,
            is_deleted=True
        )

        self.slot_c = ConsultationSlot.objects.create(
            teacher=self.instructor_1,
            date='2026-09-29',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Room 101',
            max_capacity=2,
            is_available=False,
            is_deleted=False
        )

        self.slot_d = ConsultationSlot.objects.create(
            teacher=self.instructor_2,
            date='2026-09-29',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Room 101',
            max_capacity=2,
            is_available=True,
            is_deleted=False
        )

        self.slot_e = ConsultationSlot.objects.create(
            teacher = self.instructor_1,
            date='2025-01-01',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Room 101',
            max_capacity=2,
            is_available = True,
            is_deleted = False
        )

        self.client = APIClient()


    def test_browse_available_slots_filters_inactive(self):
        self.client.force_authenticate(self.student_1)

        url = reverse('available-slot-list')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_teacher_id(self):
        self.client.force_authenticate(self.student_1)

        url = reverse('available-slot-list')

        response = self.client.get(url, {'teacher_id': self.instructor_1.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.slot_a.pk)

    def test_unauthenticated_student_discovery_fails(self):
        url = reverse('available-slot-list')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_browse_slots_excludes_past_dates(self):
        self.client.force_authenticate(self.student_1)

        url = reverse('available-slot-list')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data[0]['id'], self.slot_e.pk)
        self.assertEqual(len(response.data), 2)