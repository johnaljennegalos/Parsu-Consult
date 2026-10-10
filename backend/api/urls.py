from django.urls import path
from .views import StudentLoginView, StudentRegisterView, InstructorLoginView, InstructorRegisterView, InstructorListView, InstructorDetailView, ConsultationSlotListCreateView, ConsultationSlotDetailView, AvailableSlotListView, ConsultationBookingListCreateView, ConsultationBookingCancelView, StudentBookingHistoryView, InstructorRosterView, AttendanceUpdateView, StudentProfileMetricView, InstructorSlotListCreateView, InstructorSlotDetailView, InstructorBookingListView, InstructorBookingDecisionView, InstructorBookingAttendanceView, InstructorAnalyticsView

urlpatterns = [
    path('student/login/', StudentLoginView.as_view(), name='student-login',),
    path('student/register/', StudentRegisterView.as_view(), name='student-register'),
    path('instructor/login/', InstructorLoginView.as_view(), name='instructor-login'),
    path('instructor/register/', InstructorRegisterView.as_view(), name='instructor-register'),
    path('instructor/', InstructorListView.as_view(), name='instructor-list'),
    path('instructor/<int:pk>/', InstructorDetailView.as_view(), name='instructor-detail-view'),
    path('instructor/slots/', ConsultationSlotListCreateView.as_view(), name='consultation-slot-list-create'),
    path('instructor/slots/<int:pk>/', ConsultationSlotDetailView.as_view(), name='consultation-slot-detail'),
    path('slots/', AvailableSlotListView.as_view(), name='available-slot-list'),
    path('bookings/', ConsultationBookingListCreateView.as_view(), name='consultation-booking-list-create'),
    path('bookings/<int:pk>/cancel/', ConsultationBookingCancelView.as_view(), name='consultation-booking-cancel'),
    path('students/me/history/', StudentBookingHistoryView.as_view(), name='student-booking-history'),
    path('instructors/me/roster/', InstructorRosterView.as_view(), name='instructor-roster'),
    path('bookings/<int:pk>/attendance/', AttendanceUpdateView.as_view(), name='attendance-update'),
    path('students/me/profile-metrics/', StudentProfileMetricView.as_view(), name='student-profile-metric'),
    path('instructor/me/slots/', InstructorSlotListCreateView.as_view(), name='instructor-slot-list-create'),
    path('instructor/me/slots/<int:pk>', InstructorSlotDetailView.as_view(), name='instructor-slot-detail'),
    path('instructor/bookings/', InstructorBookingListView.as_view(), name='instructor-booking-list'),
    path('instructor/bookings/<int:pk>/decision/', InstructorBookingDecisionView.as_view(), name='instructor-booking-decision'),
    path('instructor/me/booking/<int:pk>/attendance', InstructorBookingAttendanceView.as_view(), name='instructor-booking-attendance'),
    path('instructor/me/analytics/', InstructorAnalyticsView.as_view(), name='instructor-analytics')
]