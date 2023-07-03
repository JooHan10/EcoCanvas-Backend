from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
import json
from .models import Notification
from django.utils import timezone
from campaigns.models import Participant
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from django.contrib.auth.signals import user_logged_in
from shop.models import RestockNotification, ShopProduct

channel_layer = get_channel_layer()


def send_admin_notifications(room_id):
    '''
    작성자 : 장소은
    내용 : 채팅 룸이 생성되고 상담이 진행중이지 않은 채팅 룸에 대해서 관리자에게 실시간 알림 기능 
    최초 작성일 : 2023.06.22
    '''
    message = {
        'type': 'send_admin_notification',
        'room_id': room_id,
        'message': '새로운 채팅요청이 있습니다.',
    }
    async_to_sync(channel_layer.group_send)("notification_admin_group", {
        'type': 'send_admin_notification',
        'message': json.dumps(message)
    })


def send_daily_notifications():
    '''
    작성자: 장소은
    내용: 현재 날짜로부터 3일 이내에 캠페인이 시작되는 경우 
          참가자에게 알림을 보내고, 보낸 알림 기록 

    최초 작성일: 2023.06.22
    '''
    current_datetime = timezone.now()
    campaign_start_date = current_datetime + timedelta(days=3)
    participants = Participant.objects.filter(
        is_participated=True,
        campaign__activity_start_date__range=(
            current_datetime, campaign_start_date)
    )
    for participant in participants:
        days_remain = (
            participant.campaign.activity_start_date - current_datetime).days
        message = {
            'type': 'notification_message',
            'message': f'{participant.campaign.title} 캠페인 시작까지 {days_remain}일 남았습니다.',
        }
        async_to_sync(channel_layer.group_send)("notification_group", {
            'type': 'notification_message',
            'message': json.dumps(message)
        })

        # 알림 레코드 생성
        notification = Notification.objects.create(
            user=participant.user,
            message=f'{participant.campaign.title} 캠페인 시작까지 {days_remain}일 남았습니다.',
        )
        notification.save()


scheduler = BackgroundScheduler()

scheduler.add_jobstore(DjangoJobStore(), "djangojobstore")

# scheduler.add_job(send_daily_notifications, 'interval', minutes=1)  # 테스트용
scheduler.add_job(send_daily_notifications,
                  'cron',
                  hour=18
                  )  # 매일 오후 6시에 작업 실행 예약

register_events(scheduler)

scheduler.start()


@receiver(user_logged_in)
def handle_user_logged_in(sender, request, user, **kwargs):
    '''
    작성자 : 장소은
    내용 : 로그인 시 읽지 않은 알림을 사용자에게 알려줌
    작성일 : 2023.06.25
    '''
    unread_notifications = Notification.objects.filter(
        user=user, is_read=False)
    for unread in unread_notifications:
        message = {
            'type': 'notification_message',
            'message': f'읽지 않은 알림이 있습니다.',
        }
        async_to_sync(channel_layer.group_send)("notification_login_group", {
            'type': 'notification_message',
            'message': json.dumps(message)
        })


@receiver(post_save, sender=ShopProduct)
def send_notifications(sender, instance, created, **kwargs):
    '''
    작성자 : 장소은
    내용 : 상품이 재입고 된 경우 재입고 알림신청을 한 사용자들에게 알림 기능, 알림 메세지 저장
    최초 작성일 : 2023.06.22
    '''
    if not created and instance.restocked:
        notification_group = RestockNotification.objects.filter(
            product=instance, notification_sent=False)
        for notification in notification_group:
            message = {
                'type': 'notification_message',
                'message': f'상품 {instance.product_name}이(가) 재입고되었습니다.',
            }
            async_to_sync(channel_layer.group_send)("notification_group", {
                'type': 'notification_message',
                'message': json.dumps(message)
            })

            notification.notification_sent = True  # 알림 보낸 상태 업뎃
            notification.restock_message = f'상품 {instance.product_name}이(가) 재입고되었습니다.',
            notification.save()

            notification_obj = Notification.objects.create(
                user=notification.user,
                restock=notification,
                message=message['message']
            )
            notification_obj.save()
