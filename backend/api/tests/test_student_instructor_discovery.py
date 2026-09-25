from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class InstructorSearchAndDiscoveryTest(APITestCase):
    def setUp(self):
        self.instructor_list_url = reverse('instructor-list')

        self.student_a = User.objects.create_user(
            username='studenta1',
            password='yowyow123!',
            email='stud1@test.com',
            department='CS',
            role='ST'
        )

        self.student_b = User.objects.create_user(
            username='studentb1',
            password='scrt123!',
            email='stud2@test.com',
            department='MATH',
            role='ST'
        )

        self.instructor_a = User.objects.create_user(
            username='insa1',
            password='ins456!',
            email='ins1@test.com',
            department='CS',
            specialization='Data Science',
            role='IN'
        )

        self.instructor_b = User.objects.create_user(
            username='insb1',
            password='ins789!',
            email='ins2@test.com',
            department='ENG',
            specialization='Robotics',
            role='IN'
        )

    def test_default_department_feed(self):
        self.client.force_authenticate(user=self.student_a)

        response = self.client.get(self.instructor_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], self.instructor_a.email)

        returned_emails = [instructor['email'] for instructor in response.data]
        self.assertNotIn(self.instructor_b.email, returned_emails)

    def test_global_search_returns_out_of_department_instructors(self):
        self.client.force_authenticate(user=self.student_a)

        response = self.client.get(self.instructor_list_url, {'search' : 'Robotics'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], self.instructor_b.email)

    def test_role_isolation_instructor_forbidden(self):
        self.client.force_authenticate(user=self.instructor_a)

        response = self.client.get(self.instructor_list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.instructor_list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sensitive_fields_excluded(self):
        self.client.force_authenticate(user=self.student_a)

        response = self.client.get(self.instructor_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        first_record = response.data[0]

        self.assertNotIn('password', first_record)
        self.assertNotIn('username', first_record)
        self.assertNotIn('role', first_record)
        self.assertNotIn('is_superuser', first_record)
        self.assertNotIn('is_staff', first_record)

        self.assertIn('email', first_record)
        self.assertIn('department', first_record)
        self.assertIn('specialization', first_record)

