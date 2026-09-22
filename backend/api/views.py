from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .serializers import StudentLoginSerializer


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

