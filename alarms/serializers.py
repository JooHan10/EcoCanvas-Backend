from rest_framework import serializers
from .models import Notification


class UserNotificationSerializer(serializers.ModelSerializer):
    '''
    작성자 : 장소은
    내용 : 유저의 알림 내역 조회를 위한 시리얼라이저
    작성일 : 2023.06.22
    '''

    class Meta:
        model = Notification
        fields = ['id', 'participant', 'message',
                  'created_at']
