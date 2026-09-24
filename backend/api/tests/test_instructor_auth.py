from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model


User = get_user_model()

class InstructorLoginTest(APITestCase):
    def setUp(self):
        self.login_url = reverse('instructor-login')
        self.instructor_user = User.objects.create_user(
            username='instructor1',
            password='chillproof',
            employee_id='21313141414',
            first_name='Peter',
            last_name='Stark',
            email='peter@test.com',
            role='IN',
            address='Lagonoy',
            contact_number='0912343212',
            department='CS',
            specialization='Data Science',
        )

    def test_instructor_login_success(self):
        payload = {
            'username' : 'instructor1',
            'password' : 'chillproof'
        }

        response = self.client.post(self.login_url, data=payload, format='json')

        print("LOGIN FAIL REASON:", response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('role', response.data)
        self.assertEqual(response.data['role'], 'IN')

    def test_instructor_invalid_password(self):
        payload = {
            'username' : 'instructor1',
            'password' : 'chillvillain'
        }

        response = self.client.post(self.login_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)

    def test_student_cannot_login_as_instructor(self):
        User.objects.create_user(
            username='student1',
            password='pogistudent',
            student_id='2718273618',
            first_name='John',
            last_name='Galos',
            email='john@test.com',
            role='ST'
        )

        payload = {
            'username': 'student1',
            'password': 'pogistudent'
        }

        response = self.client.post(self.login_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)

    def test_instructor_login_missing_fields(self):
        payload = {
            'username' : 'instructor1',
        }

        response = self.client.post(self.login_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)