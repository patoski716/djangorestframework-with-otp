# users/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import TempUser
from .serializers import TempUserSerializer, OTPVerifySerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = TempUserSerializer

    @swagger_auto_schema(
        request_body=TempUserSerializer,
        responses={
            201: openapi.Response(
                description='User registered successfully',
                schema=TempUserSerializer
            ),
            400: openapi.Response(
                description='Invalid input'
            ),
        }
    )
    def perform_create(self, serializer):
        temp_user = serializer.save()
        temp_user.generate_otp()
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {temp_user.otp}',
            'from@example.com',  # Replace with your actual email address
            [temp_user.email],
            fail_silently=False,
        )

class OTPVerifyView(APIView):
    @swagger_auto_schema(
        request_body=OTPVerifySerializer,
        responses={
            200: openapi.Response(
                description='OTP verified successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication token')
                    }
                )
            ),
            400: openapi.Response(
                description='Invalid OTP or username'
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            temp_user = TempUser.objects.get(username=serializer.validated_data['username'])
            user = User.objects.create_user(
                username=temp_user.username,
                email=temp_user.email,
                password=temp_user.password
            )
            temp_user.delete()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            },
            required=['username', 'password'],
        ),
        responses={
            200: openapi.Response(
                description='Login successful',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='Authentication token')
                    }
                )
            ),
            400: openapi.Response(
                description='Invalid credentials'
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Retrieve or create a token for the user
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        
        # Invalid credentials
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
