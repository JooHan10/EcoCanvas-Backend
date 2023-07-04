from django.db import models
from users.models import User
from campaigns.models import Campaign
from shop.models import ShopOrder


class Payment(models.Model):
    '''
    작성자 : 송지명
    작성날짜 : 2023.06.06
    작성내용 : 결제 시스템 모델
    업데이트 날짜 : 2023.06.22
    '''
    
    STATUS_CHOICES = (
        (0, "펀딩 결제 대기 중"),
        (1, "예약결제 취소"),
        (2, "사용자 변심"),
        (3, "상품 불만족"),
        (4, "취소 후 재결제"),
        (5, "예약결제 완료"),
        (6, "기타")
        
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount= models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True)
    merchant_uid = models.CharField(max_length=255)
    imp_uid = models.CharField(max_length=255, null=True)
    order = models.OneToOneField(ShopOrder, on_delete=models.CASCADE, null=True)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES, null=True)
    customer_uid = models.CharField(max_length=255, blank=True, null=True)
    other_status = models.CharField(max_length=50, blank=True, null=True)
    
    def get_status_display(self):
        if self.status == 6:
            return self.other_status
        else:
            status_text = dict(self.STATUS_CHOICES).get(self.status)
            return {self.status:status_text}
    
    def __str__(self):
        return self.get_status_display()
    
    
class RegisterPayment(models.Model):
    '''
    작성자 : 송지명
    작성날짜 : 2023.06.14
    작성내용 : 결제 카드 등록 모델
    업데이트 날짜 :
    '''
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    customer_uid = models.CharField(max_length=255, blank=True, null=True)
    card_number = models.CharField(max_length=100)

