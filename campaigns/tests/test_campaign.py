import os
import json
import random
import tempfile
from PIL import Image
from faker import Faker
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from rest_framework.test import APITestCase
from users.models import User
from campaigns.models import Campaign
from campaigns.serializers import CampaignSerializer


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
    최초 작성일 : 2023.06.08
    """
    size = (50, 50)
    image = Image.new("RGBA", size)
    image.save(temp_image, "png")
    return temp_image


class CampaignCreateTest(APITestCase):
    """
    작성자 : 최준영
    내용 : 캠페인 생성 테스트 클래스입니다.
    최초 작성일 : 2023.06.08
    업데이트 일자 : 2023.06.30
    """

    @classmethod
    def setUpTestData(cls):
        file_path = get_dummy_path('dummy_data.json')
        with open(file_path, encoding="utf-8") as test_json:
            test_dict = json.load(test_json)
            cls.campaign_data = test_dict
            test_json.close()
        cls.user_data = {
            "email": "test@test.com",
            "username": "John",
            "password": "Qwerasdf1234!",
        }
        cls.campaign_data["goal"] = "10000"
        cls.campaign_data["amount"] = "0"
        cls.user = User.objects.create_user(**cls.user_data)

    def setUp(self):
        self.access_token = self.client.post(reverse("log_in"), self.user_data).data[
            "access"
        ]

    def test_create_campaign(self):
        """
        캠페인 생성 테스트 함수입니다.
        임시 이미지파일과 펀딩 승인파일을 생성한 후
        펀딩정보와 같이 캠페인에 같이 POST요청을 확인하는 테스트입니다.
        """
        temp_img = tempfile.NamedTemporaryFile()
        temp_img.name = "image.png"
        image_file = arbitrary_image(temp_img)
        image_file.seek(0)
        self.campaign_data["image"] = image_file

        temp_text = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        temp_text.write("some text")
        temp_text.seek(0)
        self.campaign_data["approve_file"] = temp_text

        url = reverse("campaign_view")
        response = self.client.post(
            path=url,
            data=encode_multipart(data=self.campaign_data, boundary=BOUNDARY),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 201)


class CampaignReadTest(APITestCase):
    """
    작성자 : 최준영
    내용 : 캠페인 GET요청이 올바르게 이루어지는지 검증하는 테스트 클래스입니다.
    최초 작성일 : 2023.06.08
    업데이트 일자 : 2023.06.15
    """

    @classmethod
    def setUpTestData(cls):
        cls.campaigns = []
        list_of_domains = (
            "com",
            "co",
            "net",
            "org",
            "biz",
            "info",
            "edu",
            "gov",
        )
        cls.faker = Faker()
        first_name = cls.faker.first_name()
        last_name = cls.faker.last_name()
        company = cls.faker.company().split()[0].strip(",")
        dns_org = cls.faker.random_choices(elements=list_of_domains, length=1)[0]
        email_faker = f"{first_name}.{last_name}@{company}.{dns_org}".lower()
        date = timezone.now() + timedelta(seconds=random.randint(0, 86400))
        for _ in range(6):
            cls.user = User.objects.create_user(
                cls.faker.name() + "A1!", email_faker, cls.faker.word() + "B2@"
            )
            cls.campaigns.append(
                Campaign.objects.create(
                    title=cls.faker.sentence(),
                    content=cls.faker.text(),
                    user=cls.user,
                    members=random.randrange(100, 200),
                    campaign_start_date=date,
                    campaign_end_date=date,
                    activity_start_date=date,
                    activity_end_date=date,
                    image="",
                    status=1,
                    is_funding="False",
                    category=1,
                )
            )

    def test_get_campaign(self):
        """
        `setUpTestData` 메소드를 사용하여 테스트 사용자와 캠페인 데이터를 설정합니다.
        1. GET 요청의 status_code가 200인지 확인합니다.
        2. faker 패키지를 사용하여 10개의 더미 리뷰 데이터를 생성하고, 생성된 10개의 캠페인에 대해
        response와 serializer가 일치하는지 테스트합니다.
        """
        for i, campaign in enumerate(self.campaigns):
            url = reverse("campaign_view") + "?page=1&order=like"
            response = self.client.get(url)
            serializer = CampaignSerializer(campaign).data
            self.assertEqual(response.status_code, 200)
            for key, value in serializer.items():
                self.assertEqual(response.data["results"][i][key], value)


class CampaignDetailTest(APITestCase):
    """
    작성자 : 최준영
    내용 : 캠페인 특정캠페인 GET, UPDATE, DELETE 요청 테스트 클래스입니다.
    최초 작성일 : 2023.06.09
    업데이트 일자 :
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
        cls.new_campaign_data = {
            "title": "탄소발자국 캠페인 모집",
            "content": "더 나은 세상을 위한 지구별 눈물 닦아주기, 이제 우리가 행동에 나설 때입니다.\
                인류 역사상 가장 위대한 미션: 2050년까지 탄소중립을 실현하라",
            "members": "300",
            "campaign_start_date": "2023-06-19",
            "campaign_end_date": "2023-06-30",
            "activity_start_date": "2023-06-20",
            "activity_end_date": "2023-06-27",
            "image": "",
            "is_funding": "True",
            "status": "1",

            "goal": "1000000",
            "amount": "10000",
            "approve_file": "",
        }
        cls.user = User.objects.create_user(**cls.user_data)

    def setUp(self):
        self.access_token = self.client.post(reverse("log_in"), self.user_data).data[
            "access"
        ]
        temp_img = tempfile.NamedTemporaryFile()
        temp_img.name = "image.png"
        image_file = arbitrary_image(temp_img)
        image_file.seek(0)
        self.campaign_data["image"] = image_file.name

        temp_text = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        temp_text.write("some text")
        temp_text.seek(0)
        self.new_campaign_data["approve_file"] = temp_text

        self.campaign_data["user"] = User.objects.get(id=1)

        self.campaign = Campaign.objects.create(**self.campaign_data)
        
    def test_get_detail_campaign(self):
        """
        개별 캠페인 GET요청 테스트 함수입니다.
        """
        campaign = Campaign.objects.get(title=self.campaign_data["title"])
        url = campaign.get_absolute_url()
        response = self.client.get(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)

    def test_update_campaign(self):
        """
        캠페인 수정 테스트 함수입니다.
        임시 이미지파일과 펀딩 승인파일을 생성한 후
        수정한 뒤 PUT 요청이 잘 이루어지는지 검증하는 테스트함수입니다.
        """
        campaign = Campaign.objects.get(title=self.campaign_data["title"])
        url = campaign.get_absolute_url()
        response = self.client.put(
            path=url,
            data=self.new_campaign_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_campaign(self):
        """
        캠페인 삭제 테스트 함수입니다.
        임시 이미지파일과 펀딩 승인파일을 생성한 후
        DELETE 요청이 잘 이루어지는지 검증하는 테스트함수입니다.
        """
        campaign = Campaign.objects.get(title=self.campaign_data["title"])
        url = campaign.get_absolute_url()
        response = self.client.delete(
            path=url, 
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, 204)


class CampaignLikeTest(APITestCase):
    """
    작성자 : 최준영
    내용 : 캠페인 좋아요 POST 요청 테스트 클래스입니다.
    최초 작성일 : 2023.06.09
    업데이트 일자 :
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

        cls.campaign_data["user"] = User.objects.get(id=1)
        cls.campaign = Campaign.objects.create(**cls.campaign_data)

    def setUp(self):
        self.access_token = self.client.post(reverse("log_in"), self.user_data).data[
            "access"
        ]

    def test_like_campaign(self):
        """
        캠페인 좋아요 POST요청 테스트 함수입니다.
        """
        campaign = Campaign.objects.get(title=self.campaign_data["title"])
        url = reverse("campaign_like_view", kwargs={"campaign_id": campaign.id})
        response = self.client.post(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "좋아요 성공!")

    def test_dislike_campaign(self):
        """
        캠페인 좋아요 취소 POST요청 테스트 함수입니다.
        """
        campaign = Campaign.objects.get(title=self.campaign_data["title"])
        url = reverse("campaign_like_view", kwargs={"campaign_id": campaign.id})
        response = self.client.post(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "좋아요 성공!")

        response = self.client.post(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "좋아요 취소!")


class CampaignParticipationTest(APITestCase):
    """
    작성자 : 최준영
    내용 : 캠페인 참가 POST 요청 테스트 클래스입니다.
    최초 작성일 : 2023.06.11
    업데이트 일자 :
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
        cls.campaign_data["members"] = "1"

        cls.user = User.objects.create_user(**cls.user_data)

        cls.campaign_data["user"] = User.objects.get(id=1)
        cls.campaign = Campaign.objects.create(**cls.campaign_data)

    def setUp(self):
        self.access_token = self.client.post(reverse("log_in"), self.user_data).data[
            "access"
        ]

    def test_participate_campaign(self):
        """
        캠페인 참가 POST요청 테스트 함수입니다.
        """
        campaign = Campaign.objects.get(title=self.campaign_data["title"])
        url = reverse("campaign_participation_view", kwargs={"campaign_id": campaign.id})
        response = self.client.post(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "캠페인 참가 성공!")

    def test_cancel_participate_campaign(self):
        """
        캠페인 참가 취소 POST요청 테스트 함수입니다.
        """
        campaign = Campaign.objects.get(title=self.campaign_data["title"])
        url = reverse("campaign_participation_view", kwargs={"campaign_id": campaign.id})
        response = self.client.post(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "캠페인 참가 성공!")

        response = self.client.post(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "캠페인 참가 취소!")

    def test_max_participate_campaign(self):
        """
        캠페인 참가 정원이 이미 만석인데 신청한 경우 참가신청이 실패하는지 테스트하는 함수입니다.
        """
        campaign = Campaign.objects.get(title=self.campaign_data["title"])
        url = reverse("campaign_participation_view", kwargs={"campaign_id": campaign.id})
        response1 = self.client.post(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.data["message"], "캠페인 참가 성공!")

        second_user_data = {
            "email": "second@test.com",
            "username": "Nue",
            "password": "Qwerasdf1234!",
        }
        second_user = User.objects.create_user(**second_user_data)
        access_token2 = self.client.post(reverse("log_in"), second_user_data).data["access"]
        response2 = self.client.post(
            path=url,
            HTTP_AUTHORIZATION=f"Bearer {access_token2}",
        )
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(response2.data["message"], "캠페인 참가 정원을 초과하여 신청할 수 없습니다.")
