# # Create your views here.
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.utils import timezone
# from .models import PairSession
# from .serializers import CreateSessionSerializer, PairSessionSerializer

# class CreateSessionAPIView(APIView):

#     def post(self, request):
#         user_id = request.user.id if request.user.is_authenticated else 1

#         serializer = CreateSessionSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         session = PairSession.objects.create(
#             host_id=user_id,
#             **serializer.validated_data
#         )

#         return Response(
#             {
#                 "session_id": str(session.id),
#                 "session_code": session.session_code,
#                 "problem_id": session.problem_id,  # Changed from session.problem.id
#                 "language": session.language
#             },
#             status=status.HTTP_201_CREATED
#         )


# class JoinSessionAPIView(APIView):

#     def post(self, request):
#         user_id = request.user.id
#         session_id = request.data.get("session_id")

#         try:
#             session = PairSession.objects.get(id=session_id)
#         except PairSession.DoesNotExist:
#             return Response({"error": "Session not found"}, status=404)

#         if session.status == "ended":
#             return Response({"error": "Session already ended"}, status=400)

#         if session.guest_id:
#             return Response({"error": "Session is full"}, status=400)

#         if session.host_id == user_id:
#             return Response({"error": "Host cannot join as guest"}, status=400)

#         session.guest_id = user_id
#         session.status = "active"
#         session.started_at = timezone.now()
#         session.save()

#         return Response(PairSessionSerializer(session).data)



# class PublicSessionsAPIView(APIView):

#     def get(self, request):
#         sessions = PairSession.objects.filter(
#             is_public=True,
#             status="waiting"
#         ).order_by("-created_at")

#         return Response(
#             PairSessionSerializer(sessions, many=True).data
#         )


# class EndSessionAPIView(APIView):

#     def post(self, request, session_id):
#         user_id = request.user.id if request.user.is_authenticated else 1

#         try:
#             session = PairSession.objects.get(id=session_id)
#         except PairSession.DoesNotExist:
#             return Response({"error": "Session not found"}, status=404)

#         if session.host_id != user_id:
#             return Response({"error": "Only host can end session"}, status=403)

#         session.status = "ended"
#         session.ended_at = timezone.now()
#         session.save()

#         return Response({"message": "Session ended"})


# class GetSessionAPIView(APIView):

#     def get(self, request, session_id):
#         try:
#             session = PairSession.objects.get(id=session_id)
#         except PairSession.DoesNotExist:
#             return Response({"error": "Session not found"}, status=404)

#         return Response(PairSessionSerializer(session).data)

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import hashlib
from .models import PairSession
from .serializers import CreateSessionSerializer, PairSessionSerializer


def get_user_id(request):
    """Get unique user ID - authenticated users or anonymous by IP"""
    if request.user.is_authenticated:
        return request.user.id
    # For anonymous users, use IP address to create stable unique ID
    ip = request.META.get('REMOTE_ADDR', 'unknown')
    return int(hashlib.md5(ip.encode()).hexdigest()[:8], 16) % 1000000


class CreateSessionAPIView(APIView):
    """Create a new pair programming session"""

    def post(self, request):
        #  FIX: Try to get user_id from multiple sources
        # Priority: explicit user_id > authenticated user > username hash > IP hash
        
        user_id = None
        
        # 1. Check if frontend sent explicit user_id
        user_id = request.data.get('user_id')
        if user_id:
            user_id = int(user_id)
            print(f"Using user_id from request: {user_id}")
        
        # 2. Check if user is authenticated
        elif request.user.is_authenticated:
            user_id = request.user.id
            print(f" Using authenticated user_id: {user_id}")
        
        # 3. Generate from username
        else:
            username = request.data.get('username')
            if username:
                user_id = int(hashlib.md5(username.encode()).hexdigest()[:8], 16) % 1000000
                print(f" Generated user_id from username: {user_id}")
            else:
                # 4. Generate from IP address
                ip = request.META.get('REMOTE_ADDR', 'unknown')
                user_id = int(hashlib.md5(ip.encode()).hexdigest()[:8], 16) % 1000000
                print(f"  Generated user_id from IP: {user_id}")

        print(" Create Session Debug:")
        print(f"   User ID: {user_id}")
        print(f"   Username: {request.data.get('username')}")
        print(f"   Is Authenticated: {request.user.is_authenticated}")

        serializer = CreateSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = PairSession.objects.create(
            host_id=user_id,
            **serializer.validated_data
        )

        return Response(
            {
                "id": str(session.id),
                "session_id": str(session.id),
                "session_code": session.session_code,
                "problem_id": session.problem_id,
                "language": session.language,
                "host_id": session.host_id  
            },
            status=status.HTTP_201_CREATED
        )


class JoinSessionAPIView(APIView):
    """Join an existing pair programming session"""

    def post(self, request):
        try:
            user_id = None
            
            # 1. Check if frontend sent explicit user_id
            user_id = request.data.get('user_id')
            if user_id:
                user_id = int(user_id)
                print(f"Using user_id from request: {user_id}")
            
            # 2. Check if user is authenticated
            elif request.user.is_authenticated:
                user_id = request.user.id
                print(f" Using authenticated user_id: {user_id}")
            
            # 3. Generate from username
            else:
                username = request.data.get('username')
                if username:
                    user_id = int(hashlib.md5(username.encode()).hexdigest()[:8], 16) % 1000000
                    print(f" Generated user_id from username: {user_id}")
                else:
                    # 4. Generate from IP address
                    ip = request.META.get('REMOTE_ADDR', 'unknown')
                    user_id = int(hashlib.md5(ip.encode()).hexdigest()[:8], 16) % 1000000
                    print(f"  Generated user_id from IP: {user_id}")

            session_code = request.data.get("session_id")

            print(f"   Current User ID: {user_id}")
            print(f"   Is Authenticated: {request.user.is_authenticated}")
            print(f"   Username from request: {request.data.get('username')}")
            print(f"   Session Code Received: {session_code}")

            if not session_code:
                return Response({"error": "session_id is required"}, status=400)

            try:
                session = PairSession.objects.get(session_code=session_code)
            except PairSession.DoesNotExist:
                try:
                    session = PairSession.objects.get(id=session_code)
                except PairSession.DoesNotExist:
                    return Response({"error": "Session not found"}, status=404)

            print(f"   Session Host ID: {session.host_id}")
            print(f"   Session Guest ID: {session.guest_id}")
            print(f"   Session Status: {session.status}")

            if session.status == "ended":
                return Response({"error": "Session already ended"}, status=400)

            if session.guest_id:
                return Response({"error": "Session is full"}, status=400)

            if session.host_id == user_id:
                print(f"   Host cannot join as guest (user_id={user_id}, host_id={session.host_id})")
                return Response({"error": "Host cannot join as guest"}, status=400)

            session.guest_id = user_id
            session.status = "active"
            session.started_at = timezone.now()
            session.save()

            return Response(PairSessionSerializer(session).data)

        except Exception as e:
            print(f"    Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=400)


class PublicSessionsAPIView(APIView):
    """Get all public sessions waiting for participants"""

    def get(self, request):
        sessions = PairSession.objects.filter(
            is_public=True,
            status="waiting"
        ).order_by("-created_at")

        return Response(
            PairSessionSerializer(sessions, many=True).data
        )


class EndSessionAPIView(APIView):
    """End a pair programming session (host only)"""

    def post(self, request, session_id):
        try:
            # FIX: Get user_id from multiple sources
            user_id = None
            
            # 1. Check if frontend sent explicit user_id
            user_id = request.data.get('user_id')
            if user_id:
                user_id = int(user_id)
                print(f" Using user_id from request: {user_id}")
            
            # 2. Check if user is authenticated
            elif request.user.is_authenticated:
                user_id = request.user.id
                print(f"Using authenticated user_id: {user_id}")
            
            # 3. Generate from username
            else:
                username = request.data.get('username')
                if username:
                    user_id = int(hashlib.md5(username.encode()).hexdigest()[:8], 16) % 1000000
                    print(f" Generated user_id from username: {user_id}")
                else:
                    # 4. Generate from IP address
                    ip = request.META.get('REMOTE_ADDR', 'unknown')
                    user_id = int(hashlib.md5(ip.encode()).hexdigest()[:8], 16) % 1000000
                    print(f"  Generated user_id from IP: {user_id}")

            print(f"   Current User ID: {user_id}")
            print(f"   Is Authenticated: {request.user.is_authenticated}")

            try:
                session = PairSession.objects.get(id=session_id)
            except PairSession.DoesNotExist:
                return Response({"error": "Session not found"}, status=404)

            if session.status == "ended":
                return Response({"error": "Session already ended"}, status=400)

            print(f"   Session Host ID: {session.host_id}")
            print(f"   Current User ID: {user_id}")
            print(f"   Match: {session.host_id == user_id}")

            # Check if user is the host
            if session.host_id != user_id:
                return Response({"error": "Only host can end session"}, status=403)

            session.status = "ended"
            session.ended_at = timezone.now()
            session.save()

            return Response({"message": "Session ended"})

        except Exception as e:
            print(f"    Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=400)


class GetSessionAPIView(APIView):
    """Get session details by ID"""

    def get(self, request, session_id):
        try:
            session = PairSession.objects.get(id=session_id)
        except PairSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)

        return Response(PairSessionSerializer(session).data)