from .models import ShopOrder
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment

channel_layer = get_channel_layer()


@receiver(post_save, sender=ShopOrder)
def send_payments(sender, instance, created, **kwargs):
    '''
    작성자 : 송지명
    내용 : 결제오더 생성시 결제 모델 저장
    최초 작성일 : 2023.06.23
    '''
    if created:
       payment = Payment.objects.filter(user=instance.user).latest('created_at')
       payment.order = instance
       payment.save()
        

