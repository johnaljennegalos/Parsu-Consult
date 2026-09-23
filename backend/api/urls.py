from django.urls import path
from .views import StudentLoginView, StudentRegisterView

urlpatterns = [
    path('student/login/', StudentLoginView.as_view(), name='student-login',),
    path('student/register/', StudentRegisterView.as_view(), name='student-register')
]