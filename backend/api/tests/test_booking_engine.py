from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from api.models import ConsultationSlot, ConsultationBooking



User = get_user_model()

class BookingEngineAPITests(APITestCase):
    def setUp(self):
        self.instructor_1 = User.objects.create_user(
            role='IN',
            username='ins1',
            email='ins1@test.com'
        )

        self.student_1 = User.objects.create_user(
            role='ST',
            username='stud1',
            email='stud1@test.com'
        )

        self.student_2 = User.objects.create_user(
            role='ST',
            username='stud2',
            email='stud2@test.com'
        )

        self.instructor_slot = ConsultationSlot.objects.create(
            teacher=self.instructor_1,
            date='2026-10-15',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.client = APIClient()

    def test_successful_booking(self):
        self.client.force_authenticate(self.student_1)

        url = reverse('consultation-booking-list-create')

        response = self.client.post(url, {'slot' : self.instructor_slot.pk})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        db_query = ConsultationBooking.objects.filter(student=self.student_1, slot=self.instructor_slot, status='CONFIRMED').exists()

        self.assertTrue(db_query)

    def test_duplicate_booking_prevention(self):
        self.client.force_authenticate(self.student_1)

        url = reverse('consultation-booking-list-create')

        response = self.client.post(url, {'slot' : self.instructor_slot.pk})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        second_response = self.client.post(url, {'slot' : self.instructor_slot.pk}, format='json')

        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('slot', second_response.data)

    def test_capacity_limit_enforcement(self):
        self.client.force_authenticate(self.student_1)

        url = reverse('consultation-booking-list-create')
        response = self.client.post(url, {'slot' : self.instructor_slot.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.student_2)
        second_url = reverse('consultation-booking-list-create')
        second_response = self.client.post(second_url, {'slot' : self.instructor_slot.pk}, format='json')

        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

        active_booking = ConsultationBooking.objects.filter(slot=self.instructor_slot, status='CONFIRMED').count() == 1

        self.assertTrue(active_booking)

    def test_cancellation_frees_capacity(self):
        self.client.force_authenticate(self.student_1)

        url = reverse('consultation-booking-list-create')
        response = self.client.post(url, {'slot' : self.instructor_slot.pk}, format='json')

        booking_id = response.data['id']

        cancel_url = reverse('consultation-booking-cancel', kwargs={'pk': booking_id})
        patch_response = self.client.patch(cancel_url, {'slot': self.instructor_slot.pk, 'status': 'CANCELLED'}, format='json')
        print("CANCEL ERROR:", patch_response.data)

        self.client.force_authenticate(self.student_2)
        second_url = reverse('consultation-booking-list-create')
        second_response = self.client.post(second_url, {'slot' : self.instructor_slot.pk}, format='json')

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        confirmed_count = ConsultationBooking.objects.filter(slot=self.instructor_slot, status='CONFIRMED').count()

        self.assertTrue(confirmed_count, 1)

    def test_unauthenticated_user_blocked(self):
        self.client.logout()

        url = reverse('consultation-booking-list-create')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_student_cannot_cancel_others_booking(self):
        self.client.force_authenticate(self.student_1)
        url = reverse('consultation-booking-list-create')
        response = self.client.post(url, {'slot' : self.instructor_slot.pk}, format='json')
        booking_id = response.data['id']

        self.client.force_authenticate(self.student_2)
        patch = self.client.patch(booking_id, {'slot' : self.student_1.pk}, format='json')

        self.assertEqual(patch.status_code, status.HTTP_404_NOT_FOUND)

    def test_instructor_cannot_book_slot(self):
        self.client.force_authenticate(self.instructor_1)

        url = reverse('consultation-booking-list-create')
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_book_unavailable_slot(self):
        self.instructor_slot.is_available = False
        self.instructor_slot.save()

        self.client.force_authenticate(self.student_1)

        url = reverse('consultation-booking-list-create')
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('slot', response.data)

    def test_cannot_book_deleted_slot(self):
        self.instructor_slot.is_deleted = True
        self.instructor_slot.save()

        self.client.force_authenticate(self.student_1)
        url = reverse('consultation-booking-list-create')
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_book_nonexistent_slot(self):
        self.client.force_authenticate(self.student_1)
        url = reverse('consultation-booking-list-create')
        response = self.client.post(url, {'slot' : 9999}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_book_past_slot(self):
        self.instructor_slot.date = '2020-01-01'
        self.instructor_slot.save()

        self.client.force_authenticate(self.student_1)
        url = reverse('consultation-booking-list-create')
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('slot', response.data)

    def test_cannot_cancel_already_cancelled_booking(self):
        self.client.force_authenticate(self.student_1)
        url = reverse('consultation-booking-list-create')
        response = self.client.post(url,{'slot' : self.instructor_slot.pk}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        booking_id = response.data['id']

        patch_url = reverse('consultation-booking-cancel', kwargs={'pk': booking_id})

        first_patch = self.client.patch(patch_url, {'status': 'CANCELLED'}, format='json')
        self.assertEqual(first_patch.status_code, status.HTTP_200_OK)

        second_patch = self.client.patch(patch_url, {'status': 'CANCELLED'}, format='json')
        self.assertEqual(second_patch.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', second_patch.data)

    def test_cannot_reconfirm_cancelled_booking_via_patch(self):
        self.client.force_authenticate(self.student_1)
        url = reverse('consultation-booking-list-create')
        response = self.client.post(url,{'slot' : self.instructor_slot.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        booking_id = response.data['id']
        patch_url = reverse('consultation-booking-cancel', kwargs={'pk': booking_id})
        first_patch = self.client.patch(patch_url, {'status': 'CANCELLED'}, format='json')
        self.assertEqual(first_patch.status_code, status.HTTP_200_OK)

        second_patch = self.client.patch(patch_url, {'status': 'CONFIRMED'}, format='json')
        self.assertEqual(second_patch.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', second_patch.data)

        db_query = ConsultationBooking.objects.filter(status='CANCELLED').exists()
        self.assertTrue(db_query)
