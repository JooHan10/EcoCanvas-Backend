from rest_framework import serializers
from campaigns.models import Campaign, Funding
from .models import Payment, RegisterPayment
from iamport import Iamport
from config import settings
import time
from django.db import transaction
from django.db.models import F
import datetime


class RegisterPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisterPayment
        fields = '__all__'
    
class RegisterSerializer(serializers.ModelSerializer):
    '''
    작성자 : 송지명
    작성날짜 : 2023.06.09
    작성내용 : 결제정보 등록 시리얼라이저
    Iamport api에 카드번호를 보내 customer_uid 요청.
    요청 후 Iamport api에서 데이터 값을 받아 저장(추후 예약 시 사용)
    
    업데이트 날짜 : 2023.06.14
    '''
    expiry_at = serializers.CharField(error_messages={
            "required": "유효기간은 필수 입력 사항입니다!",
            "blank": "유효기간은 필수 입력 사항입니다!"
        }, write_only=True)
    birth = serializers.CharField(error_messages={
            "required": "생년월일은 필수 입력 사항입니다!",
            "blank": "생년월일은 필수 입력 사항입니다!"
        }, write_only=True)
    pwd_2digit = serializers.CharField(error_messages={
            "required": "비밀번호는 필수 입력 사항입니다!",
            "blank": "비밀번호는 필수 입력 사항입니다!"
        }, write_only=True)
    class Meta:
        model = RegisterPayment
        fields = ('created_at','customer_uid', 'card_number', 'expiry_at', 'birth', 'pwd_2digit')
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs['context']['request'].user
        super().__init__(*args, **kwargs)
    
    def create(self, data):
        
        get_expiry = data.get('expiry_at')
        birth = data.get('birth')
        card_number = data.get('card_number')
        pwd_2digit = data.get('pwd_2digit')
        email = self.context['request'].user.email
        customer_uid = f"{email}_{int(time.time())}"
        response ={
            'customer_uid':customer_uid,
            'card_number':card_number,
            'expiry':get_expiry,
            'birth':birth,
            'pg':'nice',
            'pwd_2digit':pwd_2digit,
        }
        return response
        
    

class PaymentScheduleSerializer(serializers.ModelSerializer):
    '''
    작성자 : 송지명
    작성날짜 : 2023.06.09
    작성내용 : 펀딩 결제용 시리얼라이저.
    캠페인 ID 및 결제 금액을 받아와 request user의 결제용 customer_uid 를 이용해 결제.
    추후 결제 취소를 위한 merchant_uid 저장.
    업데이트 날짜 : 2023.06.14
    '''
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    amount = serializers.CharField(max_length=10, write_only=True)
    selected_card = serializers.PrimaryKeyRelatedField(queryset=RegisterPayment.objects.all())

    class Meta:
        model = Payment
        fields = ('campaign','amount', 'selected_card')
        
    def create(self, data):
        campaign = data.get('campaign')
        campaign_date = campaign.campaign_end_date     
        schedules_date_default = campaign_date.replace(tzinfo=None)
        schedules_date = schedules_date_default + datetime.timedelta(days=1)
        schedules_at = int(schedules_date.timestamp())
        iamport = Iamport(imp_key=settings.IMP_KEY, imp_secret=settings.IMP_SECRET)
        customer_uid = data.get('selected_card').customer_uid
        amount = data.get('amount')
        merchant_uid = f"imp{int(time.time())}"
        user_id = self.context['request'].user
        schedules = {
            "merchant_uid": merchant_uid,
            "schedule_at": schedules_at,
            "currency": "KRW",
            "amount": amount,
            "name": user_id.username
        }
        payload = {
            'customer_uid': customer_uid,
            'schedules': [schedules]
        }
        with transaction.atomic():
            response = iamport.pay_schedule(**payload)
            # 모든 작업이 성공한 경우에만 Payment 객체 생성 및 저장
            data = Payment.objects.create(user=user_id, amount=amount, campaign=campaign, merchant_uid=merchant_uid, status="0", customer_uid=customer_uid)
            Funding.objects.filter(campaign=campaign).update(amount=F('amount')+amount)

        return response
        
