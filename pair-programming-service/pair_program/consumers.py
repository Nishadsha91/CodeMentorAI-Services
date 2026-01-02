import json
import hashlib
from urllib.parse import unquote
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import PairSession
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async


def get_user_id_from_username(username):
    """Calculate user ID from username (matches REST API logic)"""
    if username:
        return int(hashlib.md5(username.encode()).hexdigest()[:8], 16) % 1000000
    return None


class PairSessionConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"pair_{self.session_id}"

        self.user = self.scope.get("user")
        print("User:", self.user)

        # Get username and user_id from query parameters
        query_string = self.scope.get("query_string", b"").decode()
        username = None
        user_id = None
        
        if query_string:
            params = dict(param.split("=") for param in query_string.split("&") if "=" in param)
            username = params.get("username")
            if username:
                username = unquote(username)  # Decode URL-encoded username
            
            # NEW: Try to get user_id from query parameter
            user_id_param = params.get("user_id")
            if user_id_param:
                try:
                    user_id = int(user_id_param)
                    print(f"Got user_id from query param: {user_id}")
                except (ValueError, TypeError):
                    print(f"  Invalid user_id in query param: {user_id_param}")
                    user_id = None

        # Calculate user_id if not provided in query params
        if self.user and not isinstance(self.user, AnonymousUser) and self.user.is_authenticated:
            self.user_id = self.user.id
            self.username = self.user.username
            print(f"Auth user: {self.user_id} ({self.username})")
        elif user_id:
            #  Use user_id from query parameter
            self.user_id = user_id
            self.username = username
            print(f"Using user_id from query param: {self.user_id} ({username})")
        elif username:
            # Fall back to generating from username
            self.user_id = get_user_id_from_username(username)
            self.username = username
            print(f"  Generated user_id from username: {self.user_id} ({username})")
        else:
            print(" No user identification")
            await self.close()
            return

        try:
            session = await self.get_session()
            print(" Session found:", session.id)
        except PairSession.DoesNotExist:
            print(" Session not found")
            await self.close()
            return

        # Check if user is allowed in this session
        allowed_users = [session.host_id]
        if session.guest_id is not None:
            allowed_users.append(session.guest_id)

        print(f"   User ID: {self.user_id}")
        print(f"   Host ID: {session.host_id}")
        print(f"   Guest ID: {session.guest_id}")
        print(f"   Allowed users: {allowed_users}")

        if self.user_id not in allowed_users:
            print(f" User {self.user_id} not allowed in session (allowed: {allowed_users})")
            await self.close()
            return

        self.session = session
        self.role = "host" if self.user_id == session.host_id else "guest"
        print(f" User role: {self.role}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(" WebSocket accepted")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_join",
                "user_id": self.user_id,
                "username": self.username,
                "role": self.role,
            }
        )

    # async def disconnect(self, close_code):
    #     await self.channel_layer.group_discard(
    #         self.room_group_name,
    #         self.channel_name
    #     )
    async def disconnect(self, close_code):
        print(f" WebSocket disconnect: {self.user_id} ({self.username})")
        # Broadcast user left event
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                "user_id": self.user_id,
                "username": self.username,
                "role": self.role
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get("type")

        if event_type == "editor_change":
            await self.handle_editor_change(data)
        elif event_type == "chat_message":
            await self.handle_chat_message(data)
        elif event_type == "cursor_position":
            await self.handle_cursor_position(data)
        elif event_type == "session_ended":
            # Only host can end session
            if self.role == "host":
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "session_ended",
                        "user_id": self.user_id
                    }
                )

    async def handle_editor_change(self, data):
        # Permission: observer can't edit
        if self.session.mode == "observer" and self.role != "host":
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "editor_update",
                "code": data.get("code"),
                "language": data.get("language"),
                "user_id": self.user_id,
                "username": self.username,
            }
        )

    async def handle_chat_message(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_broadcast",
                "message": data.get("message"),
                "user_id": self.user_id,
                "username": self.username,
            }
        )

    async def handle_cursor_position(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "cursor_update",
                "line": data.get("line"),
                "column": data.get("column"),
                "user_id": self.user_id,
                "username": self.username,
            }
        )

    async def editor_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "codeChanged",
            "content": event["code"],
            "language": event["language"],
            "user_id": event["user_id"],
            "username": event["username"],
        }))

    async def chat_broadcast(self, event):
        await self.send(text_data=json.dumps({
            "type": "chatReceived",
            "message": event["message"],
            "user": event["username"],
            "user_id": event["user_id"],
        }))

    async def cursor_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "cursor_update",
            "line": event["line"],
            "column": event["column"],
            "user_id": event["user_id"],
            "username": event["username"],
        }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_join",
            "user_id": event["user_id"],
            "username": event["username"],
            "role": event["role"],
        }))
    
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_left",
            "user_id": event["user_id"],
            "username": event["username"],
            "role": event["role"],
        }))

    async def session_ended(self, event):
        await self.send(text_data=json.dumps({
            "type": "session_ended",
            "ended_by": event["user_id"]
        }))


    @database_sync_to_async
    def get_session(self):
        return PairSession.objects.get(id=self.session_id)