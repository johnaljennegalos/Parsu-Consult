from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import StudentLoginSerializer, StudentRegistrationSerializer, InstructorLoginSerializer, InstructorRegistrationSerializer


class StudentLoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = StudentLoginSerializer(data=request.data, context={'request' : request})

        if not serializer.is_valid():
            if 'password' in serializer.errors or 'username' in serializer.errors:
                return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role' : user.role
        }, status=status.HTTP_200_OK)


class StudentRegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InstructorLoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InstructorLoginSerializer(data=request.data, context={'request' : request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']

        if user is None:
            return Response({'errors' : 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.role != 'IN':
            return Response({'error' : 'Account is not registered as Instructor'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role' : user.role
        }, status=status.HTTP_200_OK)


class InstructorRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InstructorRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


