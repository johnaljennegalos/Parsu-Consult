from django.test import TestCase
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
    NotificationSerializer
)

# Create your tests here.

User = get_user_model()

class SerializerTestCase(TestCase):

    def setUp(self):
        self.student_user = User.objects.create_user(
            email="galos123.pbox@parsu.edu.ph",
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
            email='obias223.pbox@parsu.edu.ph',
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
            'student_id' : '82387420',
            'email' : 'romero231.pbox@parsu.edu.ph',
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
            'email' : 'patron.pbox@parsu.edu.ph',
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
        self.assertEqual(serializer.data['email'], 'galos123.pbox@parsu.edu.ph')
        self.assertEqual(serializer.data['role'], 'ST')
        self.assertEqual(serializer.data['first_name'], 'John Aljenne')
        self.assertEqual(serializer.data['last_name'], 'Galos')