# users/serializers.py
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import TempUser, OTP

class TempUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempUser
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class OTPVerifySerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            temp_user = TempUser.objects.get(username=data['username'])
            if temp_user.otp != data['otp']:
                raise serializers.ValidationError("Invalid OTP")
        except TempUser.DoesNotExist:
            raise serializers.ValidationError("Invalid username or OTP")
        return data
