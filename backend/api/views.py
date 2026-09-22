from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


class StudentLoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        return Response({
            'access': 'fake-access-jwt-token',
            'refresh': 'fake-refresh-jwt-token',
            'role': 'ST'
        }, status=status.HTTP_200_OK)

