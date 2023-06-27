from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from django.conf import settings
from .views import DetailScheduleReceiptAPIView
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import register_events


def payment_check():
    """
    작성자 : 송지명
    내용 : Payment의 status를 Campaign status 체크 후 변경 실행해주는 메서드.
          매일 오전 8시에 체크하여 실행하도록 하였습니다.
    최초 작성일 : 2023.06.24
    업데이트 일자 :
    """
    payment_scheduler = BackgroundScheduler()
    payment_scheduler.add_jobstore(DjangoJobStore(), "djangojobstore")
    register_events(payment_scheduler)
    
    @payment_scheduler.scheduled_job(CronTrigger(hour=8))
    def check():
         DetailScheduleReceiptAPIView().check_payment_status()

    payment_scheduler.start()

