from django.urls import path
from .views import StudentLoginView, StudentRegisterView, InstructorLoginView, InstructorRegisterView, InstructorListView, InstructorDetailView

urlpatterns = [
    path('student/login/', StudentLoginView.as_view(), name='student-login',),
    path('student/register/', StudentRegisterView.as_view(), name='student-register'),
    path('instructor/login/', InstructorLoginView.as_view(), name='instructor-login'),
    path('instructor/register/', InstructorRegisterView.as_view(), name='instructor-register'),
    path('instructor/', InstructorListView.as_view(), name='instructor-list'),
    path('instructor/<int:pk>', InstructorDetailView.as_view(), name='instructor-detail-view')
]