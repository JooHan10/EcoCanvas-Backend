import os
import json
import tempfile
from PIL import Image
from django.urls import reverse
from rest_framework.test import APITestCase
from users.models import User
from campaigns.models import Campaign, CampaignComment


def get_dummy_path(file_name):
    """
    작성자 : 최준영
    내용 : 더미데이터 로드를 위한 함수입니다.
    최초 작성일 : 2023.06.30
    """
    directory = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(directory, file_name)


def arbitrary_image(temp_image):
    """
    작성자 : 최준영
    내용 : 테스트용 임의 이미지 생성 함수입니다.
    최초 작성일 : 2023.06.09
    """
    size = (50, 50)
    image = Image.new("RGBA", size)
    image.save(temp_image, "png")
    return temp_image


class CampaignCommentCreateReadTest(APITestCase):
    """
    작성자 : 최준영
    내용 : 캠페인 댓글 GET, POST 요청 테스트 클래스입니다.
    최초 작성일 : 2023.06.09
    업데이트 일자 : 2023.06.30
    """
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {
            "email": "test@test.com",
            "username": "John",
            "password": "Qwerasdf1234!",
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

        cls.user = User.objects.create_user(**cls.user_data)

        cls.campaign_data['user'] = User.objects.get(id=1)
        cls.campaign = Campaign.objects.create(**cls.campaign_data)

        cls.comment_data = {
            "content": "좋은 캠페인이네요"
        }

    def setUp(self):
        self.access_token = self.client.post(reverse("log_in"), self.user_data).data[
            "access"
        ]

    def test_create_campaign_comment(self):
        """
        캠페인 댓글 POST 요청 테스트함수입니다.
        """
        url = reverse("campaign_comment_view", kwargs={"campaign_id": self.campaign.id})
        response = self.client.post(
            path=url,
            data=self.comment_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 201)

    def test_read_campaign_comment(self):
        """
        캠페인 댓글 GET 요청 테스트함수입니다.
        """
        url = reverse("campaign_comment_view", kwargs={"campaign_id": self.campaign.id})
        response = self.client.get(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)


class CampaignCommentUpdateDeleteTest(APITestCase):
    """
    작성자 : 최준영
    내용 : 캠페인 댓글 UPDATE, DELETE 요청 테스트 클래스입니다.
    최초 작성일 : 2023.06.09
    업데이트 일자 : 2023.06.30
    """
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {
            "email": "test@test.com",
            "username": "John",
            "password": "Qwerasdf1234!",
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

        cls.user = User.objects.create_user(**cls.user_data)

        cls.campaign_data['user'] = User.objects.get(id=1)
        cls.campaign = Campaign.objects.create(**cls.campaign_data)

        cls.comment_data = {
            "content": "좋은 캠페인이네요"
        }
        cls.new_comment_data = {
            "content": "좋은 캠페인이네요. 꼭 참여하고 싶습니다!"
        }
        cls.comment_data['user'] = User.objects.get(id=1)
        cls.comment_data['campaign'] = Campaign.objects.get(id=1)
        cls.comment = CampaignComment.objects.create(**cls.comment_data)

    def setUp(self):
        self.access_token = self.client.post(reverse("log_in"), self.user_data).data[
            "access"
        ]

    def test_update_campaign_comment(self):
        """
        캠페인 댓글 PUT 요청 테스트함수입니다.
        """
        comment = CampaignComment.objects.get(content=self.comment_data['content'])
        url = comment.get_absolute_url()
        response = self.client.put(
            path=url,
            data=self.new_comment_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_campaign_comment(self):
        """
        캠페인 댓글 DELETE 요청 테스트함수입니다.
        """
        comment = CampaignComment.objects.get(content=self.comment_data['content'])
        url = comment.get_absolute_url()
        response = self.client.delete(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 204)
