from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model



User = get_user_model()

class StudentLoginTest(APITestCase):
    def setUp(self):
        self.login_url = reverse('student-login')
        self.student_user = User.objects.create_user(
            username='student1',
            password='pogistudent',
            student_id='2718273618',
            first_name='John',
            last_name='Galos',
            email='john@test.com',
            role='ST'
        )

    def test_student_login_success(self):
        payload = {
            'username' : 'student1',
            'email' : 'john@test.com',
            'password' : 'pogistudent',
        }

        response = self.client.post(self.login_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('role', response.data)
        self.assertEqual(response.data['role'], 'ST')

    def test_student_invalid_password(self):
        payload = {
            'username' : 'student1',
            'email' : 'john@test.com',
            'password' : 'uglystudent'
        }

        response = self.client.post(self.login_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertIn('error', response.data)

    def test_instructor_cannot_login_as_student(self):
        self.instructor = User.objects.create_user(
            username='instructor1',
            password='chillproof',
            employee_id='35462383',
            first_name='Juan',
            last_name='Cruz',
            email='juan@test.com',
            role='IN'
        )

        payload = {
            'username' : 'instructor1',
            'password' : 'chillproof'
        }

        response = self.client.post(self.login_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertIn('error', response.data)

    def test_student_login_missing_fields(self):
        payload = {
            'username' : 'student1',
            'password' : ''
        }

        response = self.client.post(self.login_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertIn('password', response.data)

class StudentRegistrationTest(APITestCase):
    def setUp(self):
        self.register_url = reverse('student-register')

    def test_student_registration_success(self):
        payload = {
            'username' : 'johndoe123',
            'email' : 'johnstudent@test.com',
            'password' : 'johnghost1!',
            'address' : 'Camarines Sur',
            'contact_number' : '09123456890',
            'first_name' : 'John',
            'last_name' : 'Doe',
            'student_id' : '1234567890',
            'course' : 'BSCS',
            'year_level' : '3',
            'section' : 'B',
        }

        response  = self.client.post(self.register_url, data=payload, format='json')
        print("REGISTRATION ERRORS:", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        print("USERS IN DB:", list(User.objects.values('id', 'username', 'email')))
        user = User.objects.get(username='johndoe123')
        self.assertEqual(user.email, 'johnstudent@test.com')
        self.assertEqual(user.role, 'ST')
        self.assertTrue(user.check_password('johnghost1!'))


    def test_student_duplicate_registration(self):
        User.objects.create_user(
            username='existinguser',
            email='johnstudent@test.com',
            student_id='123457890',
        )

        payload = {
            'username' : 'johndoe123',
            'email' : 'johnstudent@test.com',
            'password' : 'johnghost1!',
            'address' : 'Camarines Sur',
            'contact_number' : '09123456890',
            'first_name' : 'John',
            'last_name' : 'Doe',
            'student_id' : '1234567890',
            'course' : 'BSCS',
            'year_level' : '3',
            'section' : 'B',
        }

        response = self.client.post(self.register_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_student_weak_password(self):
        payload = {
            'username' : 'johndoe123',
            'email' : 'johnstudent@test.com',
            'password' : '123!',
            'address' : 'Camarines Sur',
            'contact_number' : '09123456890',
            'first_name' : 'John',
            'last_name' : 'Doe',
            'student_id' : '1234567890',
            'course' : 'BSCS',
            'year_level' : '3',
            'section' : 'B',
        }

        response = self.client.post(self.register_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertEqual(User.objects.count(), 0)

    def test_student_missing_required_fields(self):
        payload = {
            'username' : 'johndoe123',
            'email' : 'johnstudent@test.com',
            'password' : '123!',
            'address' : 'Camarines Sur',
            'contact_number' : '09123456890',
            'first_name' : 'John',
            'last_name' : 'Doe',
            'student_id' : '1234567890',
            'course' : 'BSCS',
            'year_level' : '3',
            'section' : 'B',
        }

        del payload['student_id']

        response = self.client.post(self.register_url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('student_id', response.data)
        self.assertEqual(User.objects.count(), 0)

    def test_student_privilege_escalation(self):
        payload = {
            'username' : 'johndoe123',
            'email' : 'johnstudent@test.com',
            'password' : '1234567890!',
            'address' : 'Camarines Sur',
            'contact_number' : '09123456890',
            'first_name' : 'John',
            'last_name' : 'Doe',
            'student_id' : '1234567890',
            'course' : 'BSCS',
            'year_level' : '3',
            'section' : 'B',
            'role' : 'AD',
        }

        response = self.client.post(self.register_url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='johndoe123')
        self.assertEqual(user.role, 'ST')
        self.assertNotEqual(user.role, 'AD')