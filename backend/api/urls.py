from django.urls import path
from .views import StudentLoginView, StudentRegisterView, InstructorLoginView

urlpatterns = [
    path('student/login/', StudentLoginView.as_view(), name='student-login',),
    path('student/register/', StudentRegisterView.as_view(), name='student-register'),
    path('instructor/login', InstructorLoginView.as_view(), name='instructor-login')
]