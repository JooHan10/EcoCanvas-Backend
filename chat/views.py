from rest_framework.views import APIView
from chat.models import Room, Message
from users.models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from collections import Counter
from chat.serializers import RoomSerializer
from django.db.models import Q
from alarms.signals import send_admin_notifications


class RoomView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        작성자 : 박지홍
        내용 : 채팅을위한 Room을 만드는 기능.
            - 이미 같은 대상과의 채팅방이 존재 할 경우 만들어진 방번호를 반환한다.
        최초 작성일 : 2023.06.06
        업데이트 일자 : 2023.06.15
        #06.15 : 1:1 통신만 존재함으로 인해 기존의 N:N 통신 기반 함수를 덜어냄.
        """
        # counselor = User.objects.filter(is_admin=True).first()

        room = Room.objects.filter(advisee=request.user).values('id').first()
        if room:
            send_admin_notifications(room['id'])
            return Response(room, status=status.HTTP_201_CREATED)
        else:
            return Response(None, status=status.HTTP_400_BAD_REQUEST)


class ActiveRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room = Room.objects.filter(Q(is_active=True) & Q(counselor=None))
        serializer = RoomSerializer(room, many=True)
        return Response(serializer.data, status=200)
