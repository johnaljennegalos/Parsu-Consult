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
