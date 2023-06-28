from django.urls import reverse
from rest_framework.test import APITestCase
from users.models import User
from .models import (
    ShopProduct,
    ShopCategory,
    ShopImageFile,
    RestockNotification
)
from datetime import timedelta
from django.utils import timezone
import random
from PIL import Image
from io import BytesIO
from .signals import send_notifications


def arbitrary_image():
    '''
    작성자:장소은
    내용: arbitrary_image()함수와 BytesIO를 사용하여 50x50픽셀의 임시 이미지(png형식) 생성
    작성일:2023.06.13
    '''
    size = (50, 50)
    image = Image.new("RGBA", size)
    temp_img = BytesIO()
    image.save(temp_img, format="PNG")
    temp_img.name = "image.png"
    temp_img.seek(0)
    return temp_img


class ProductPostTest(APITestCase):
    '''
    작성자: 장소은
    내용: 일반유저가 상품 post 했을 때, admin유저가 post했을 때 testcode 작성
          다중이미지 업로드 기능 업데이트
    작성일: 2023.06.07
    업데이트: 2023.06.23
    '''
    @classmethod
    def setUpTestData(cls):
        date = timezone.now() + timedelta(seconds=random.randint(0, 86400))
        cls.user_data = {
            "email": "test@google.com",
            "username": "testuser",
            "password": "Xptmxm123@456"
        }
        cls.user = User.objects.create_user(**cls.user_data)
        cls.admin = User.objects.create_superuser(
            email="adminuser@test.com", username="관리자소은", password="Xptmxm123@456")
        cls.admin_data = {"email": "adminuser@test.com",
                          "password": "Xptmxm123@456"}

        cls.category_data = {
            'category_name': "카테고리"
        }
        cls.category = ShopCategory.objects.create(**cls.category_data)
        cls.product_data = {
            'product_name': "상품",
            'product_desc': "테스트",
            'category': cls.category.id,
            'product_date': date,
            'product_price': 10000,
            'product_stock': 123,
            "images": [
                {
                    "id": 1,
                    "product": 1,
                    "image_file": ""
                }]
        }

        image_file = arbitrary_image()
        cls.product_data["images"][0]["image_file"] = image_file

    def setUp(self):
        self.admin_access_token = self.client.post(
            reverse('log_in'), self.admin_data).data['access']
        self.access_token = self.client.post(
            reverse('log_in'), self.user_data).data['access']

    def test_user_post_product(self):
        image_file = arbitrary_image()
        self.product_data["images"][0]["image_file"] = image_file
        self.product_data["uploaded_images"] = [image_file]
        url = reverse("category_sortby_product_view", kwargs={
                      "category_id": self.category.id})
        response = self.client.post(
            path=url,
            data=self.product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}",
        )
        self.assertEqual(response.status_code, 201)

    def test_not_admin_post_product(self):
        response = self.client.post(
            path=reverse("category_sortby_product_view", kwargs={
                         "category_id": self.category.id}),
            data=self.product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )

        self.assertEqual(response.status_code, 403)


class ProductListViewAPITest(APITestCase):
    '''
    작성자 : 장소은
    내용 : 상품의 전체 목록 GET 요청, 쿼리매개변수 별 GET, 검색 GET요청에 대한 테스트
    작성일 : 2023.06.23
    '''

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('product_sortby_view')

        date = timezone.now() + timedelta(seconds=random.randint(0, 86400))

        cls.category_data = {
            'category_name': "카테고리"
        }
        cls.category = ShopCategory.objects.create(**cls.category_data)
        cls.product_data = {
            'product_name': "상품",
            'product_desc': "테스트",
            'category': cls.category,
            'product_date': date,
            'product_price': 10000,
            'product_stock': 123,
            "images": [
                {
                    "id": 1,
                    "product": 1,
                    "image_file": ""
                }]
        }

        image_file = arbitrary_image()
        cls.product_data["images"][0]["image_file"] = image_file

    def test_product_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_sort_by_hits(self):
        response = self.client.get(self.url, {'sort_by': 'hits'})
        self.assertEqual(response.status_code, 200)

    def test_search_query(self):
        search_query = '에코백'
        response = self.client.get(self.url, {'search_query': search_query})
        self.assertEqual(response.status_code, 200)


class ProductUpdateTest(APITestCase):
    '''
    작성자 : 장소은
    내용 : 상품 상세 조회, 수정, 삭제 테스트(유저 / 관리자)
    작성일 : 2023.06.23
    '''

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            email="adminuser@test.com", username="관리자소은", password="Xptmxm123@456")
        cls.admin_data = {"email": "adminuser@test.com",
                          "password": "Xptmxm123@456"}

        date = timezone.now() + timedelta(seconds=random.randint(0, 86400))

        cls.user_data = {
            "email": "test@google.com",
            "username": "testuser",
            "password": "Xptmxm123@456"
        }
        cls.user = User.objects.create_user(**cls.user_data)

        cls.category_data = {
            'category_name': "카테고리"
        }
        cls.category = ShopCategory.objects.create(**cls.category_data)
        cls.product_data = {
            'product_name': "상품",
            'product_desc': "테스트",
            'category': cls.category,
            'product_date': date,
            'product_price': 10000,
            'product_stock': 123
        }
        cls.product = ShopProduct.objects.create(
            **cls.product_data)

        image_data = {
            "id": 1,
            "product": cls.product,
            "image_file": ""
        }
        cls.image = ShopImageFile.objects.create(**image_data)
        cls.product.images.set([cls.image])
        cls.product = ShopProduct.objects.create(
            **cls.product_data)

        cls.url = reverse('product_detail_view', kwargs={
            "product_id": cls.product.id})
        cls.updated_product_data = {
            'product_name': "수정 상품",
            'product_desc': "수정 테스트",
            'product_price': 20000,
            'product_stock': 50
        }

    def setUp(self):
        self.access_token = self.client.post(
            reverse("log_in"), self.user_data).data["access"]
        self.admin_access_token = self.client.post(
            reverse('log_in'), self.admin_data).data['access']

    def test_user_product_put(self):
        '''
        권한이 없는 일반유저가 PUT할 때 테스트 
        '''
        response = self.client.put(
            self.url,
            data=self.updated_product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_product_put(self):
        '''
        관리자가 PUT할 때 테스트 
        '''
        response = self.client.put(
            self.url,
            data=self.updated_product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}",
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_product_delete(self):
        '''
        관리자가 DELETE할 때 테스트 
        '''
        response = self.client.delete(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.admin_access_token}",
        )
        self.assertEqual(response.status_code, 204)


class ProductRestockNotificatinonTest(APITestCase):
    '''
    내용 : 재입고 알림 신청
    '''
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            email="adminuser@test.com", username="관리자소은", password="Xptmxm123@456")
        cls.admin_data = {"email": "adminuser@test.com",
                          "password": "Xptmxm123@456"}

        date = timezone.now() + timedelta(seconds=random.randint(0, 86400))

        cls.user_data = {
            "email": "test@google.com",
            "username": "testuser",
            "password": "Xptmxm123@456"
        }
        cls.user = User.objects.create_user(**cls.user_data)

        cls.category_data = {
            'category_name': "카테고리"
        }
        cls.category = ShopCategory.objects.create(**cls.category_data)
        cls.product_data = {
            'product_name': "상품",
            'product_desc': "테스트",
            'category': cls.category,
            'product_date': date,
            'product_price': 10000,
            'product_stock': 0,
            'sold_out': True
        }
        cls.product = ShopProduct.objects.create(
            **cls.product_data)

        image_data = {
            "id": 1,
            "product": cls.product,
            "image_file": ""
        }
        cls.image = ShopImageFile.objects.create(**image_data)
        cls.product.images.set([cls.image])
        cls.product = ShopProduct.objects.create(
            **cls.product_data)

        cls.url = reverse('restock_notification_view', kwargs={
                          "product_id": cls.product.id})

    def setUp(self):
        self.access_token = self.client.post(
            reverse("log_in"), self.user_data).data["access"]

    def test_post_restock_notification(self):
        '''
        상품 품절 시 재입고 알림 POST 테스트
        '''
        response = self.client.post(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 201)

    def test_already_restock_notification(self):
        '''
        상품 재입고 알림을 이미 구독 중인 경우의 테스트 
        '''
        RestockNotification.objects.create(
            product=self.product, user=self.user)

        response = self.client.post(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(
            response.data['message'],
            '이미 재입고 알림을 구독 하셨습니다.'
        )


class ProductOrderTest(APITestCase):
    '''
    내용 : 상품 주문
    '''
    @classmethod
    def setUpTestData(cls):
        date = timezone.now() + timedelta(seconds=random.randint(0, 86400))

        cls.user_data = {
            "email": "test@google.com",
            "username": "testuser",
            "password": "Xptmxm123@456"
        }
        cls.user = User.objects.create_user(**cls.user_data)

    def setUp(self):
        self.access_token = self.client.post(
            reverse("log_in"), self.user_data).data["access"]

    def test_product_order(self):
        '''
        상품 주문을 위한 테스트
        '''
        response = self.client.post(
            self.url,
            data=self.product_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 201)


# class SendNotificationsTest(APITestCase):
#     '''
#     상품 재입고 시 알림 구독자들에게 알림 전송 테스트
#     '''
#     @classmethod
#     def setUpTestData(cls):
#         date = timezone.now() + timedelta(seconds=random.randint(0, 86400))

#         cls.user_data = {
#             "email": "test@google.com",
#             "username": "testuser",
#             "password": "Xptmxm123@456"
#         }
#         cls.user = User.objects.create_user(**cls.user_data)

#         cls.category_data = {
#             'category_name': "카테고리"
#         }
#         cls.category = ShopCategory.objects.create(**cls.category_data)
#         cls.product_data = {
#             'product_name': "상품",
#             'product_desc': "테스트",
#             'restocked': True,
#             'category': cls.category,
#             'product_date': date,
#             'product_price': 10000,
#             'product_stock': 123,
#             "images": [
#                 {
#                     "id": 1,
#                     "product": 1,
#                     "image_file": ""
#                 }]
#         }

#         image_file = arbitrary_image()
#         cls.product_data["images"][0]["image_file"] = image_file

#     def test_send_notifications(self):
#         notification = RestockNotification.objects.create(
#             user=self.user, product=self.product)
#         send_notifications(sender=ShopProduct,
#                            instance=self.product, created=False)

#         notification.refresh_from_db()
#         self.assertTrue(notification.notification_sent)
        # self.assertEqual(notification.restock_message,
        #                  f"상품 {self.product.product_name}이(가) 재입고되었습니다.")

    # restock_created_at = models.DateTimeField(
    #     auto_now_add=True)
    # notification_sent = models.BooleanField(default=False)
    # restock_message = models.CharField(max_length=255, null=True, blank=True)
