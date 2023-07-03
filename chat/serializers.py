from rest_framework import serializers
from chat.models import Room, Message



class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"

class MessageSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()

    def get_user_id(self, obj):
        return obj.user_id.email

    class Meta:
        model = Message
        fields = ('message', 'user_id',)
