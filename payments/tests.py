from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from users.models import User
from campaigns.models import Campaign
from .models import Payment, RegisterPayment
from faker import Faker
from config import settings
import tempfile, json
from PIL import Image
import os


def arbitrary_image(temp_text):
    """
    작성자 : 최준영
    내용 : 테스트용 임의 이미지 생성 함수입니다.
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    """
    size = (50, 50)
    image = Image.new("RGBA", size)
    image.save(temp_text, "png")
    return temp_text

def get_dummy_path(file_name):
    """
    작성자 : 최준영
    내용 : 더미데이터 로드를 위한 함수입니다.
    최초 작성일 : 2023.06.30
    """
    directory = os.path.dirname(os.path.abspath(__file__))
    campaigns_directory = os.path.dirname(directory)
    tests_directory = os.path.join(campaigns_directory, 'campaigns', 'tests')
    return os.path.join(tests_directory, file_name)

class PaymentTest(APITestCase):
    '''
    작성자: 송지명
    내용: 결제 카드 등록 및 예약결제 테스트 코드
    작성일: 2023.06.12
    업데이트날짜 : 2023.06.14
    '''

    @classmethod
    def setUpTestData(cls):
        cls.faker = Faker()
        cls.username = User.objects.create_user(email="testuser@test.com", username="test", password="Xptmxm123@456")
        cls.user_data = {"email": "testuser@test.com", "password": "Xptmxm123@456"}        
        cls.register_data = {
            "card_number": settings.CARD_NUMBER,
            "expiry": settings.EXPIRY_AT,
            "birth": settings.BIRTH,
            "pwd_2digit": settings.PWD_2DIGIT
        }
        cls.fail_register_data ={
            "card_number": settings.CARD_NUMBER[:-1],
            "expiry": settings.EXPIRY_AT,
            "birth": settings.BIRTH,
            "pwd_2digit": settings.PWD_2DIGIT
        }
        cls.payment_data = {
            'merchant_uid' : 'Merchant'+ cls.user_data['email'],
            'imp_uid' : 'IMP' + cls.user_data['email'],
            'amount': '1000'
        }
            
        file_path = get_dummy_path('dummy_data.json')
        with open(file_path, encoding="utf-8") as test_json:
            test_dict = json.load(test_json)
            cls.campaign_data = test_dict
            test_json.close()
        temp_img = tempfile.NamedTemporaryFile()
        temp_img.name = "image.png"
        image_file = arbitrary_image(temp_img)
        image_file.seek(0)
        cls.campaign_data["image"] = image_file.name
        cls.campaign_data['user'] = User.objects.get(id=cls.username.id)

        cls.campaign = Campaign.objects.create(**cls.campaign_data)
        cls.campaign_id = cls.campaign.id
           
    def setUp(self):
        self.access_token = self.client.post(reverse('log_in'), self.user_data).data['access']
        self.client = APIClient()
    def test_register_payment(self):
        '''
        결제정보 등록 테스트 코드
        '''
        response = self.client.post(
            path=reverse("register_payment"),
            data=self.register_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEquals(response.status_code, 201)
    def test_fail_register_payment(self):
        '''
        결제정보 등록 실패 테스트 코드
        '''
        response = self.client.post(
            path=reverse("register_payment"),
            data=self.fail_register_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEquals(response.status_code, 400)    
        
    def test_create_payment_schedule(self):
        '''
        결제정보 등록 후 예약결제 테스트 코드
        '''
        card_data = self.client.post(
            path=reverse("register_payment"),
            data=self.register_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        selected_card_data = card_data.data['card_number']
        selected_data = RegisterPayment.objects.get(card_number=selected_card_data)
        selected_data_id = selected_data.id
        schedule_data = {
            "campaign": self.campaign.id,  
            "amount": '1000',
            "selected_card": selected_data_id
        }
        response = self.client.post(
            path=reverse("schedule_payment", kwargs={'pk': 1}),
            data=schedule_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEquals(response.status_code, 200)
        return response
    
    def test_fail_create_payment_schedule(self):
        '''
        결제정보 등록 후 예약결제 실패 테스트 코드
        '''
        card_data = self.client.post(
            path=reverse("register_payment"),
            data=self.register_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        selected_card_data = card_data.data['card_number']
        selected_data = RegisterPayment.objects.get(card_number=selected_card_data)
        selected_data_id = selected_data.id
        schedule_data = {
            "campaign": self.campaign.id,  
            "selected_card": selected_data_id
        }
        response = self.client.post(
            path=reverse("schedule_payment", kwargs={'pk': 1}),
            data=schedule_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEquals(response.status_code, 400)
        
    def test_register_payment_view(self):
        '''
        결제정보 조회 테스트코드
        '''
        response = self.client.get(
            path=reverse("register_payment"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEquals(response.status_code, 200)
    
    
    def test_view_payment_schedule(self):
        '''
        예약결제 확인 테스트 코드
        '''
        payment = self.test_create_payment_schedule()
        payment_data = payment.data[0].get('customer_uid')
        payment_pk = Payment.objects.get(customer_uid=payment_data).pk
        response = self.client.get(reverse('schedule_payment', kwargs={'pk': payment_pk}),
                                   HTTP_AUTHORIZATION=f"Bearer {self.access_token}",)
        self.assertEqual(response.status_code, 200)
        
    def test_payment(self):
        '''
        결제모델 생성 테스트 코드
        '''
        response= self.client.post(reverse('receipt_payment', kwargs={'user_id': self.username.id}),
                                   data=self.payment_data,
                                   HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
                                   )
        self.assertEqual(response.status_code, 201)
        return response
        
    def test_refund_scheudle(self):
        '''
        예약결제취소 테스트 코드
        '''
        schedule = self.test_create_payment_schedule()
        schedule_data = schedule.data[0].get('merchant_uid')
        schedule_pk = Payment.objects.get(merchant_uid=schedule_data).pk
        response = self.client.post(reverse('schedule_receipt_payment', kwargs={'pk':schedule_pk}),
                                    HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.assertEqual(response.status_code, 200)
        