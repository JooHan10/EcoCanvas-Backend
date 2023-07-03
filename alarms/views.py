from django.shortcuts import render
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from .serializers import UserNotificationSerializer
from .models import Notification
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class CustomPagination(PageNumberPagination):
    '''
    작성자: 장소은
    내용 : 페이지네이션을 위한 커스텀페이지네이션
    작성일: 2023.06.16
    '''
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 60


class NotificationListAPIView(APIView):
    '''
    작성자 : 장소은
    내용 : 유저 캠페인 알림/재입고 알림 조회 기능, 개별 삭제/일괄 삭제 기능 
    작성일 : 2023.06.22
    수정일 : 2023.06.25
    '''
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request):
        notifications = Notification.objects.filter(
            user=request.user.id).order_by('-created_at')

        unread_notifications = notifications.filter(is_read=False)
        unread_notifications.update(is_read=True)

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(notifications, request)
        serializer = UserNotificationSerializer(
            result_page,
            many=True
        )
        return paginator.get_paginated_response(serializer.data)

    def delete(self, request):
        user = request.user.id
        notification_id = request.data.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(
                    id=notification_id,
                    user=user
                )
                notification.delete()
                return Response(status=204)

            except Notification.DoesNotExist:
                return Response({'error': '알림내역을 찾을 수 없습니다.'}, status=404)

        else:
            notifications = Notification.objects.filter(user=user)
            notifications.delete()
            return Response(status=204)
