from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
import requests
from .serializers import (RegisterSerializer,UserSerializer,ForgotPasswordSerializer,)
from Auth.events.publisher import publish_user_created_event  
import logging


logger = logging.getLogger(__name__)
# Replace all print() with logger.info()

token_generator = PasswordResetTokenGenerator()


class RegisterView(APIView):
    def post(self, request):

        serializer = RegisterSerializer(data=request.data)
        logger.info("Incoming register data:", request.data)

        if serializer.is_valid():
            user = serializer.save()
            logger.info("User created in Auth-Service:", user.id)

            # PASSING TO RABBITMQ
            event = {
                "event": "user.created",
                "user_id": user.id,
                "email": user.email,
                "full_name": user.username,
                "role": "Student",
            }

            logger.info("Publishing event to RabbitMQ:", event)
            publish_user_created_event(event)

            return Response({"message": "User registered successfully"}, status=201)

        logger.info("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=400)

# LOGIN
class LoginView(APIView):
    def post(self, request):
        logger.info("LOGIN PAYLOAD RECEIVED:", request.data)

        email = request.data.get("email", "").lower()      
        password = request.data.get("password")
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=400)

        username = user_obj.username.lower()               
        user = authenticate(username=username, password=password)

        if user is None:
            return Response({"error": "Invalid credentials"}, status=400)

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data
        })

# LOGOUT
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=200)
        except:  
            return Response({"error": "Invalid token"}, status=400)


# FORGOT PASSWORD
class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "If an account exists, a reset link was sent."})

        uid = urlsafe_base64_encode(force_bytes(user.id))
        token = token_generator.make_token(user)

        reset_url = f"http://localhost:5173/reset-password/{uid}/{token}/"

        send_mail(
            "Reset Your Password",
            f"Use this link to reset your password:\n\n{reset_url}",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return Response({"message": "Reset link sent successfully."})


# RESET PASSWORD
class ResetPasswordView(APIView):
    def post(self, request, uid, token):
        new_password = request.data.get("new_password")

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except:
            return Response({"error": "Invalid link"}, status=400)

        if not token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successful"})


# GOOGLE LOGIN
class GoogleLoginView(APIView):
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "No code provided"}, status=400)

        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": "http://localhost:5173/google/callback",
                "grant_type": "authorization_code",
            }
        ).json()

        if "access_token" not in token_response:
            return Response({"error": "Invalid Google code"}, status=400)

        access_token = token_response["access_token"]

        userinfo = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        email = userinfo["email"].lower()
        name = userinfo.get("name", "")

        username = email.split("@")[0].lower()
        if User.objects.filter(username=username).exists():
            username += "_g"

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": username, "first_name": name}
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data
        })



# GITHUB LOGIN
class GithubLoginView(APIView):
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "Code not provided"}, status=400)

        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": "http://localhost:5173/github/callback",

            },
            headers={"Accept": "application/json"}
        ).json()

        if "access_token" not in token_response:
            return Response({"error": "Invalid GitHub code"}, status=400)

        access_token = token_response["access_token"]

        userinfo = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        emails = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()

        email = None
        for e in emails:
            if e.get("primary"):
                email = e.get("email").lower()

        if not email:
            return Response({"error": "Email not available"}, status=400)

        username = userinfo["login"].lower()
        name = userinfo.get("name") or username

        if User.objects.filter(username=username).exists():
            username = username + "_gh"

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": username, "first_name": name}
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data
        })
