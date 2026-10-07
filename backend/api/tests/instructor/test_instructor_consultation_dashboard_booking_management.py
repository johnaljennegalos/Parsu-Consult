from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from api.models import ConsultationSlot, ConsultationBooking


User = get_user_model()

class InstructorConsultationDashboardBookingManagement(APITestCase):
    def setUp(self):
        self.instructor_a = User.objects.create_user(
            role='IN',
            username='insa',
            email='insa@test.com'
        )

        self.instructor_b = User.objects.create_user(
            role='IN',
            username='insb',
            email='insb@test.com'
        )

        self.student_a = User.objects.create_user(
            role='ST',
            username='stud',
            email='stud@test.com'
        )

        self.slot_a1 = ConsultationSlot.objects.create(
            teacher=self.instructor_a,
            date='2026-10-15',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.slot_a2 = ConsultationSlot.objects.create(
            teacher=self.instructor_a,
            date='2026-10-15',
            start_time='12:00:00',
            end_time='13:00:00',
            location='Faculty Room',
            max_capacity=2,
            is_available=True,
            is_deleted=False
        )

        self.slot_b1 = ConsultationSlot.objects.create(
            teacher=self.instructor_b,
            date='2026-10-15',
            start_time='10:00:00',
            end_time='11:00:00',
            location='Faculty Room',
            max_capacity=1,
            is_available=True,
            is_deleted=False
        )

        self.booking_pending_1 = ConsultationBooking.objects.create(
            slot=self.slot_a1,
            student=self.student_a,
            status='PENDING',
        )

        self.booking_pending_2 = ConsultationBooking.objects.create(
            slot=self.slot_a2,
            student=self.student_a,
            status='PENDING',
        )

        self.booking_confirmed = ConsultationBooking.objects.create(
            slot=self.slot_a1,
            student=self.student_a,
            status='CONFIRMED',
        )

        self.booking_rejected = ConsultationBooking.objects.create(
            slot=self.slot_a1,
            student=self.student_a,
            status='REJECTED',
            rejection_reason='Pre-requisite missing'
        )

        self.booking_isolate_reject = ConsultationBooking.objects.create(
            slot=self.slot_b1,
            student=self.student_a,
            status='REJECTED',
            rejection_reason='Pre-requisite missing'
        )


        self.client = APIClient()

    def test_list_bookings_success_and_isolation(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_booking_ids = [booking['id'] for booking in response.data]
        returned_slot_ids = [booking['slot'] for booking in response.data]

        self.assertIn(self.booking_pending_1.pk, returned_booking_ids)
        self.assertIn(self.slot_a1.pk, returned_slot_ids)

        self.assertNotIn(self.booking_isolate_reject.pk, returned_booking_ids)
        self.assertNotIn(self.slot_b1.pk, returned_slot_ids)

        self.assertEqual(len(response.data), 4)

    def test_list_bookings_status_query_filter(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-list')
        response = self.client.get(url, {'status' : 'pending'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertTrue(all(item['status'] == 'PENDING' for item in response.data))
        self.assertEqual(len(response.data), 2)

    def test_list_bookings_unauthorized_for_students(self):
        self.client.force_authenticate(self.student_a)

        url = reverse('instructor-booking-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_bookings_unauthenticated_fails(self):
        self.client.logout()

        url = reverse('instructor-booking-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_confirm_booking_success(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-decision', kwargs={'pk': self.booking_pending_2.pk})
        response = self.client.patch(url, {'status' : 'CONFIRMED'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking_pending_2.refresh_from_db()
        booking_status = self.booking_pending_2.status
        self.assertEqual('CONFIRMED', booking_status)

    def test_reject_booking_with_reason_success(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-decision', kwargs={'pk': self.booking_pending_2.pk})
        response = self.client.patch(url, {'status' : 'REJECTED', "rejection_reason": "Pre-requisite missing"}, format='json')

        self.booking_pending_2.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        booking_status = self.booking_pending_2.status
        self.assertEqual('REJECTED', booking_status)

        rejection_reason = self.booking_pending_2.rejection_reason
        self.assertEqual('Pre-requisite missing', rejection_reason)

    def test_reject_booking_missing_reason_fails(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-decision', kwargs={'pk': self.booking_pending_2.pk})
        response = self.client.patch(url, {'status' : 'REJECTED', "rejection_reason": " "}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rejection_reason', response.data)
        self.booking_pending_2.refresh_from_db()
        self.assertEqual(self.booking_pending_2.status, 'PENDING')


    def test_confirm_booking_triggers_slot_capacity_closure(self):
        self.client.force_authenticate(self.instructor_a)

        self.booking_confirmed.delete()

        url = reverse('instructor-booking-decision', kwargs={'pk': self.booking_pending_1.pk})
        response = self.client.patch(url, {'status' : 'CONFIRMED'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.slot_a1.refresh_from_db()
        self.assertFalse(self.slot_a1.is_available)

    def test_confirm_booking_exceeding_capacity_fails(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-decision', kwargs={'pk': self.booking_pending_1.pk})
        response = self.client.patch(url, {'status' : 'CONFIRMED'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('slot' in response.data or 'non_field_errors' in response.data or 'detail' in response.data)

    def test_decision_on_non_pending_booking_returns_404(self):
        self.client.force_authenticate(self.instructor_a)

        url = reverse('instructor-booking-decision', kwargs={'pk': self.booking_confirmed.pk})
        response = self.client.patch(url, {'status' : 'CONFIRMED', "rejection_reason": "Change of mind"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cross_teacher_decision_returns_404(self):
        self.client.force_authenticate(self.instructor_b)

        url = reverse('instructor-booking-decision', kwargs={'pk': self.booking_pending_1.pk})
        response = self.client.patch(url, {"status": "CONFIRMED"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.booking_pending_1.refresh_from_db()
        self.assertIn(self.booking_pending_1.status, 'PENDING')