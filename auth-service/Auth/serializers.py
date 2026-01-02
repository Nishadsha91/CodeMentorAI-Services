from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,validators=[validate_password])
    class Meta:
        model = User
        fields = ["username", "email", "password" ]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
        }

    def validate_email(self, value):
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists")
        return email

    def validate_username(self, value):
        username = value.lower()
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists")
        return username

    def create(self, validated_data):
        validated_data["email"] = validated_data["email"].lower()
        validated_data["username"] = validated_data["username"].lower()
        user = User.objects.create_user(**validated_data)
        return user




class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "date_joined"]



class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()



class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return attrs
