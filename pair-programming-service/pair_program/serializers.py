from rest_framework import serializers
from .models import PairSession

class CreateSessionSerializer(serializers.ModelSerializer):
    problem_id = serializers.IntegerField(required=True)

    class Meta:
        model = PairSession
        fields = ["language", "mode", "is_public", "problem_id"]
        extra_kwargs = {
            'language': {'required': False, 'default': 'javascript'},
            'mode': {'required': False, 'default': 'collaborative'},
            'is_public': {'required': False, 'default': True},
        }


class JoinSessionSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()


class PairSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PairSession
        fields = "__all__"