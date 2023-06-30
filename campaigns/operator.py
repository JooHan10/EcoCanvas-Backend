from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .views import CampaignStatusChecker
from apscheduler.triggers.cron import CronTrigger


def start():
    """
    작성자 : 최준영
    내용 : 캠페인 status 체크 실행 함수입니다.
    최초 작성일 : 2023.06.08
    업데이트 일자 : 2023.06.30
    """
    campaign_scheduler = BackgroundScheduler()
    campaign_scheduler.add_jobstore(DjangoJobStore(), "djangojobstore")

    @campaign_scheduler.scheduled_job(CronTrigger(hour=7), name='check_campaign_status')
    def check_campaign_status_job():
        CampaignStatusChecker.check_campaign_status()

    @campaign_scheduler.scheduled_job(CronTrigger(hour=7, minute=50), name='check_funding_success')
    def check_funding_success_job():
        CampaignStatusChecker.check_funding_success()

    campaign_scheduler.start()
