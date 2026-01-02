
from django.urls import path
from .consumers import PairSessionConsumer

websocket_urlpatterns = [
    path("ws/pair/<uuid:session_id>/", PairSessionConsumer.as_asgi()),
]
