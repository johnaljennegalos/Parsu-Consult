from django.urls import path
from .views import StudentLoginView, StudentRegisterView, InstructorLoginView, InstructorRegisterView, InstructorListView, InstructorDetailView, ConsultationSlotListCreateView, ConsultationSlotDetailView, AvailableSlotListView, ConsultationBookingListCreateView, ConsultationBookingCancelView

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
    path('bookings/<int:pk>/cancel/', ConsultationBookingCancelView.as_view(), name='consultation-booking-cancel')
]