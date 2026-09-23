from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .serializers import StudentLoginSerializer, StudentRegistrationSerializer


class StudentLoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = StudentLoginSerializer(data=request.data, context={'request' : request})

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        return Response({
            'access': 'fake-access-jwt-token',
            'refresh': 'fake-refresh-jwt-token',
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