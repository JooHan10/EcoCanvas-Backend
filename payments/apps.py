from django.apps import AppConfig
from django.conf import settings


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'

    def ready(self):
        if settings.SCHEDULER_DEFAULT:
            from . import operator

            operator.payment_check()