from django.urls import reverse
from rest_framework.test import APITestCase
from users.models import User
from .models import Notification
from rest_framework import status


class NotificationReadTest(APITestCase):
    '''
    작성자 : 장소은
    내용 : 알림 내역 조회/삭제 테스트 코드 
    작성일 : 23.07.05
    '''
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {
            "email": "test@google.com",
            "username": "testuser",
            "password": "Xptmxm123@456"
        }
        cls.user = User.objects.create_user(**cls.user_data)

    def setUp(self):
        self.access_token = self.client.post(
            reverse('log_in'), self.user_data).data['access']

    def test_notification_list(self):
        url = reverse('notification_list')
        response = self.client.get(
            url,
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notification_list_pagination(self):
        for _ in range(10):
            Notification.objects.create(user=self.user, message="테스트 알림")

        url = reverse('notification_list')
        response = self.client.get(
            url,
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)  # 전체 알림 개수 확인
        self.assertEqual(len(response.data['results']), 6)  # 페이지당 알림 개수 확인

    def test_notification_delete_all(self):
        url = reverse('notification_list')
        response = self.client.delete(
            url,
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
