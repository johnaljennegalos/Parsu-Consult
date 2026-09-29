from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from api.models import ConsultationSlot

User = get_user_model()

class InstructorSlotTest(APITestCase):
    def setUp(self):
        self.instructor_a = User.objects.create_user(
            role='IN',
            username='insa123',
            email='insa@test.com'
        )

        self.instructor_b = User.objects.create_user(
            role='IN',
            username='insb123',
            email='insb@test.com'
        )

        self.student_a = User.objects.create_user(
            role='ST',
            username='stud123',
            email='stud@test.com'
        )

        self.client = APIClient()

    def test_create_slot_success(self):
        self.client.force_authenticate(self.instructor_a)

        payload = {
            'date' : '2026-09-29',
            'location' : 'Faculty Room',
            'start_time' : '10:00:00',
            'end_time' : '11:00:00',
            'max_capacity' : 1
        }

        url = reverse('consultation-slot-list-create')

        response = self.client.post(url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ConsultationSlot.objects.count(), 1)
        self.assertEqual(response.data['teacher'], self.instructor_a.pk)

    def test_create_slot_past_datetime_fails(self):
        self.client.force_authenticate(self.instructor_a)

        payload = {
            'date' : '2025-09-29',
            'location' : 'Faculty Room',
            'start_time' : '10:00:00',
            'end_time' : '11:00:00',
            'max_capacity' : 1
        }

        url = reverse('consultation-slot-list-create')

        response = self.client.post(url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data)
        self.assertEqual(response.data['date'][0], "Cannot create or update a slot in the past.")

    def test_instructor_isolation(self):
        slot_a = ConsultationSlot.objects.create(
            teacher=self.instructor_a,
            date='2026-09-29',
            location='Faculty Room',
            start_time='10:00:00',
            end_time='11:00:00',
            max_capacity=1
        )

        self.client.force_authenticate(self.instructor_b)

        list_url = reverse('consultation-slot-list-create')
        detail_url = reverse('consultation-slot-detail', kwargs={'pk': slot_a.pk})

        list_response = self.client.get(list_url)
        detail_response = self.client.get(detail_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data, [])
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_soft_delete_slot(self):
        slot_a = ConsultationSlot.objects.create(
            teacher=self.instructor_a,
            date='2026-09-29',
            location='Faculty Room',
            start_time='10:00:00',
            end_time='11:00:00',
            max_capacity=1
        )

        self.client.force_authenticate(self.instructor_a)

        url = reverse('consultation-slot-detail', kwargs={'pk' : slot_a.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(ConsultationSlot.objects.get(pk=slot_a.pk).is_deleted)

        slot_list_create_url = reverse('consultation-slot-list-create')
        slot_list_create_url_response = self.client.get(slot_list_create_url)

        self.assertEqual(slot_list_create_url_response.data, [])



        # self.instructor_user = User.objects.create_user(
        #     role='IN',
        #     username='ins123',
        #     email='ins@test.com'
        # )
        #
        # self.student_user = User.objects.create_user(
        #     role='ST',
        #     username='stud123',
        #     email='stud@test.com'
        # )

    # def test_unauthenticated_access_blocked(self):
    #     instructor_slot_url = reverse('consultation-slot-list-create')
    #     slot_url = reverse('available-slot-list')
    #     booking_url = reverse('consultation-booking-cancel', kwargs={'pk' : self.instructor_user.pk})
    #
    #     instructor_slot_url_response = self.client.get(instructor_slot_url)
    #     slot_url_response = self.client.get(slot_url)
    #     booking_url_response = self.client.get(booking_url)
    #
    #     self.assertEqual(instructor_slot_url_response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     self.assertEqual(slot_url_response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     self.assertEqual(booking_url_response.status_code, status.HTTP_401_UNAUTHORIZED)
    #
    # def test_student_cannot_access_instructor_endpoints(self):
    #     self.client.force_authenticate(self.student_user)
    #
    #     url = reverse('consultation-slot-list-create')
    #
    #     get_response = self.client.get(url)
    #     post_response = self.client.post(url)
    #
    #     self.assertEqual(get_response.status_code, status.HTTP_403_FORBIDDEN)
    #     self.assertEqual(post_response.status_code, status.HTTP_403_FORBIDDEN)