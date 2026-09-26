from http.client import responses

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class InstructorDetailTest(APITestCase):
    def setUp(self):

        self.student_a = User.objects.create_user(
            role='ST',
            department='CS',
            username='stud1',
            email='stud1@test.com'
        )

        self.instructor_a = User.objects.create_user(
            role='IN',
            department='CS',
            username='ins1',
            email='ins1@test.com'
        )

        self.student_b = User.objects.create_user(
            role='ST',
            department='MATH',
            username='stud2',
            email='stud2@test.com'
        )

    def test_retrieve_instructor_detail_success(self):
        self.client.force_authenticate(user=self.student_a)

        url = reverse('instructor-detail-view', kwargs={'pk' : self.instructor_a.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data['email'], self.instructor_a.email)
        self.assertNotIn('password', response.data)
        self.assertNotIn('role', response.data)

    def test_retrieve_student_id_returns_404(self):
        self.client.force_authenticate(self.student_a)

        url = reverse('instructor-detail-view', kwargs={'pk' : self.student_b.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_instructor_returns_404(self):
        self.client.force_authenticate(self.student_a)

        url = reverse('instructor-detail-view', kwargs={'pk' : 93838})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_unauthenticated_and_role_access(self):
        url = reverse('instructor-detail-view', kwargs={'pk' : self.instructor_a.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.instructor_a)
        second_url = reverse('instructor-detail-view', kwargs={'pk' : self.instructor_a.pk})
        second_response = self.client.get(second_url)
        self.assertEqual(second_response.status_code, status.HTTP_403_FORBIDDEN)