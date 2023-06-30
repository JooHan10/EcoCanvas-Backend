from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from datetime import datetime, timedelta
from django.utils import timezone
from django.apps import AppConfig
from django.conf import settings
from .models import Participant, Campaign
from .views import check_campaign_status
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import register_events


def start():
    """
    작성자 : 최준영
    내용 : 캠페인 status 체크 실행 함수입니다.
    Blocking이 아닌 BackgroundScheduler를 활용하여 백그라운드에서 작동합니다.
    
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    """
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "djangojobstore")
    register_events(scheduler)

    # @scheduler.scheduled_job('cron', minute = '*/1', name = 'check')
    @scheduler.scheduled_job("cron", hour="16", name="check")
    def check():
        check_campaign_status()

    scheduler.start()


