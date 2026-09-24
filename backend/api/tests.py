from multiprocessing.connection import address_type

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APITestCase
from rest_framework.test import APIRequestFactory
from .models import ConsultationSlot, Appointment, Notification
from django.contrib.auth import get_user_model
from .serializers import (
    UserGeneralSerializer,
    StudentRegistrationSerializer,
    InstructorRegistrationSerializer,
    ConsultationSlotSerializer,
    ConsultationSlotDetailSerializer,
    AppointmentSerializer,
    AppointmentDetailSerializer,
    NotificationSerializer, ChangePasswordSerializer
)

# Create your tests here.

User = get_user_model()

class SerializerTestCase(TestCase):

    def setUp(self):
        self.student_user = User.objects.create_user(
            email="galos123@example.com",
            username='el patron',
            password="galos123",
            first_name='John Aljenne',
            last_name='Galos',
            role='ST',
            student_id='1209338493',
            course='BSCS',
            year_level='3',
            section='B'
        )

        self.instructor_user = User.objects.create_user(
            email='obias223@test.com',
            password='obias123',
            username='gringo',
            first_name='John',
            last_name='Obias',
            role='IN',
            employee_id='9287374384',
            department='CS'
        )

    def test_student_registration_serializer(self):
        payload = {
            'username' : 'janeromero231',
            'student_id' : '82387420',
            'email' : 'romero231@example.com',
            'first_name' : 'Jane',
            'last_name' : 'Romero',
            'password' : 'prettyhello321',
            'contact_number' : '091234567890',
            'address' : 'Goa Camarines Sur',
            'course' : 'BSCS',
            'year_level' : '1',
            'section' : 'A',
        }

        serializer = StudentRegistrationSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.role, 'ST')
        self.assertTrue(user.check_password('prettyhello321'))

    def test_instructor_registration_serializer(self):
        payload = {
            'employee_id' : '272394893',
            'email' : 'patron@test.com',
            'username' : 'patron',
            'first_name' : 'John',
            'last_name' : 'Galos',
            'password' : 'elpatron123',
            'department' : 'CS'
        }

        serializer = InstructorRegistrationSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.role, 'IN')
        self.assertTrue(user.check_password('elpatron123'))


    def test_user_general_serializer_omits_password(self):
        serializer = UserGeneralSerializer(self.student_user)
        self.assertNotIn('password', serializer.data)
        self.assertEqual(serializer.data['email'], 'galos123@example.com')
        self.assertEqual(serializer.data['role'], 'ST')
        self.assertEqual(serializer.data['first_name'], 'John Aljenne')
        self.assertEqual(serializer.data['last_name'], 'Galos')


    def test_consultation_slot_teacher_read_only(self):
        payload = {
            'teacher' : self.instructor_user.id,
            'start_time' : '09:00:00',
            'end_time' : '10:00:00',
            'max_capacity' : '3',
            'location' : 'IT Faculty Building',
        }

        serializer = ConsultationSlotSerializer(data=payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn('teacher', serializer.validated_data)


    def test_notification_patch_only_is_read(self):
        instance = Notification.objects.create(
            recipient=self.student_user,
            is_read=False,
            message='Original Message',
            title='OG title',
        )

        payload = {
            'recipient' : self.student_user.id,
            'appointment' : self.instructor_user,
            'title' : 'Hacked title',
            'message' : 'Spoofed message',
            'is_read' : True,
            'created_at' : '10:00:00'
        }

        serializer = NotificationSerializer(instance, data=payload, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn('is_read', serializer.validated_data)
        self.assertEqual(serializer.validated_data['is_read'], True)

        self.assertNotIn('message', serializer.validated_data)
        self.assertNotIn('title', serializer.validated_data)
        self.assertNotIn('recipient', serializer.validated_data)



#create a test for password
#class PasswordManagementTests(APITestCase): test_change_password_success test_change_password_incorrect_old_password test_change_password_weak_new_password test_change_password_unauthenticated test_registration_hashes_password
class PasswordManagementTest(APITestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            email = 'johh_student@email.com',
            username = 'johnStudent',
            password = 'OldStudentPassword',
            role = 'ST',
            first_name = 'John',
            last_name = 'Korver'
        )

        self.instructor = User.objects.create_user(
            email = 'peter_instructor@email.com',
            username = 'peterInstructor',
            password = 'OldInstructorPassword',
            role = 'IN',
            first_name = 'Peter',
            last_name = 'Doe'
        )

        self.factory = APIRequestFactory()

    def test_student_can_change_password(self):

        request = self.factory.post('api/change-password/')
        request.user = self.student

        payload = {
            'old_password' : 'OldStudentPassword',
            'new_password' : 'NewStudentPassword'
        }

        serializers = ChangePasswordSerializer(data=payload, context={'request' : request})

        self.assertTrue(serializers.is_valid(), serializers.errors)
        serializers.save()
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('NewStudentPassword'))
        self.assertFalse(self.student.check_password('OldStudentPassword'))

    def test_instructor_can_change_password(self):
        request = self.factory.post('api/change-password/')
        request.user = self.instructor

        payload = {
            'old_password' : 'OldInstructorPassword',
            'new_password' : 'giantThree'
        }

        serializers = ChangePasswordSerializer(data=payload, context={'request' : request})

        self.assertTrue(serializers.is_valid(), serializers.errors)
        serializers.save()
        self.instructor.refresh_from_db()
        self.assertTrue(self.instructor.check_password('giantThree'))
        self.assertFalse(self.instructor.check_password('OldInstructorPassword'))

    def test_change_password_incorrect_old_password(self):
        request = self.factory.post('api/change-password/')
        request.user = self.student

        payload = {
            'old_password' : 'WrongPassword123',
            'new_password' : 'ThisIsAValidNewPassword'
        }

        serializers = ChangePasswordSerializer(data=payload, context={'request' : request})

        self.assertFalse(serializers.is_valid())
        self.assertIn('old_password', serializers.errors)
        self.student.refresh_from_db()
        self.assertFalse(self.student.check_password('WrongPassword123'))
        self.assertTrue(self.student.check_password('OldStudentPassword'))

    def test_change_password_weak_new_password(self):
        request = self.factory.post('api/change-password/')
        request.user = self.student

        payload = {
            'old_password' : 'OldStudentPassword',
            'new_password' : 'password'
        }

        serializers = ChangePasswordSerializer(data=payload, context={'request' : request})

        self.assertFalse(serializers.is_valid())
        self.assertIn('new_password', serializers.errors)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password('OldStudentPassword'))

    def test_change_password_unauthenticated(self):
        request = self.factory.post('api/change-password/')
        request.user = AnonymousUser()

        payload = {
            'old_password' : 'oldlookingauthpass',
            'new_password' : 'newnewnewnew'
        }

        serializers = ChangePasswordSerializer(data=payload, context={'request' : request})

        self.assertFalse(serializers.is_valid())
        self.assertIn('old_password', serializers.errors)

    def test_registration_hashes_password(self):

        payload = {
            'employee_id' : '272394893',
            'email' : 'patron@test.com',
            'username' : 'patron',
            'first_name' : 'John',
            'last_name' : 'Galos',
            'password' : 'elpatron123',
            'department' : 'CS'
        }

        serializers = InstructorRegistrationSerializer(data=payload)

        self.assertTrue(serializers.is_valid(), serializers.errors)
        user = serializers.save()

        user.refresh_from_db()

        self.assertNotEqual(user.password, 'elpatron123')
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password('elpatron123'))




