
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from faker import Faker
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from PIL import Image
import tempfile
from users.models import User
from campaigns.models import (
    Campaign,
    Funding
)
from campaigns.serializers import (
    CampaignSerializer,
    CampaignCreateSerializer,
)


class Test(APITestCase):

    camp_data = [
        {
            "user": "1",
            "title": "TestCamp",
            "content": "TEST Text",
            "members": "10",
            "campaign_start_date": "2022-05-21",
            "campaign_end_date": "2022-05-23",
            "activity_start_date": "2022-05-30",
            "activity_end_date": "2022-06-30",
            "is_funding": False
        },
        {
            "user": "1",
            "title": "TestCamp2",
            "content": "TEST Text2",
            "members": "12",
            "campaign_start_date": "2022-05-22",
            "campaign_end_date": "2022-05-23",
            "activity_start_date": "2022-05-30",
            "activity_end_date": "2022-06-30",
            "is_funding": False
        }
    ]

    def create_user(self, email, password):
        user = self.client.post(reverse("sign_up"), {
                                "email": email, "username": "test1", "password": password, "re_password": password})
        return self.client.post(reverse("log_in"), {"email": email, "password": password}).data['access']

    def test_case_get_participating(self):
        email = "test@test.com"
        password = "Qadpye12uo!"
        access_token = self.create_user(email, password)

        parti_url = reverse("participating_campaign")
        create_camp_url = reverse("campaign_view")
        token = f'Bearer {access_token}'
        client = APIClient()

        for camp in self.camp_data:
            self.client.post(path=create_camp_url, data=camp,
                             headers={"Authorization": token})

        get = self.client.get(path=parti_url, headers={"Authorization": token})
        self.assertAlmostEqual(len(self.camp_data), (len(get.data)))

    def test_case_get_review(self):
        email = "test@test.com"
        password = "Qadpye12uo!"
        access_token = self.create_user(email, password)
        token = f'Bearer {access_token}'
        client = APIClient()
        parti_url = reverse("participating_campaign")
        create_camp_url = reverse("campaign_view")
        for camp in self.camp_data:
            self.client.post(path=create_camp_url, data=camp,
                             headers={"Authorization": token})
        get = self.client.get(path=parti_url, headers={"Authorization": token})

        create_review_url = reverse("campaign_review_view", args=[1])
        user_review_url = reverse("campaign_user_review")
        review_data = [
            {
                "title": "Test Review",
                "content": "test review content"
            },
            {
                "title": "Test Review2",
                "content": "test review content2"
            }
        ]
        for review in review_data:
            self.client.post(path=create_review_url, data=review,
                             headers={"Authorization": token})

        review = self.client.get(path=user_review_url, headers={
                                 "Authorization": token})
        self.assertAlmostEqual(len(review_data), (len(review.data)))

    def test_case_get_commend(self):
        email = "test@test.com"
        password = "Qadpye12uo!"
        access_token = self.create_user(email, password)
        token = f'Bearer {access_token}'
        client = APIClient()
        parti_url = reverse("participating_campaign")
        create_camp_url = reverse("campaign_view")
        for camp in self.camp_data:
            self.client.post(path=create_camp_url, data=camp,
                             headers={"Authorization": token})
        get = self.client.get(path=parti_url, headers={"Authorization": token})

        create_commend_url = reverse("campaign_comment_view", args=[1])
        user_commned_url = reverse("campaign_comment")

        commend_data = [
            {
                "content": "test review content"
            },
            {
                "content": "test review content2"
            }
        ]

        for commend in commend_data:
            status = self.client.post(path=create_commend_url, data=commend, headers={
                                      "Authorization": token})

        comment = self.client.get(path=user_commned_url, headers={
                                  "Authorization": token})
        self.assertAlmostEqual(len(commend_data), (len(comment.data)))

    def test_case_get_like(self):
        email = "test@test.com"
        password = "Qadpye12uo!"
        access_token = self.create_user(email, password)
        token = f'Bearer {access_token}'
        client = APIClient()
        parti_url = reverse("participating_campaign")
        create_camp_url = reverse("campaign_view")
        # for camp in self.camp_data:
        #     self.client.post(path=create_camp_url, data=camp,
        #                  headers={"Authorization": token})
        self.client.post(path=create_camp_url, data=self.camp_data[0], headers={"Authorization": token})
        get = self.client.get(path=parti_url, headers={"Authorization": token})
        for i in range(0, len(self.camp_data)):
            like_url = reverse("campaign_like_view", args=[i+1])
            status = self.client.post(path=like_url, headers={
                                      "Authorization": token})

        user_like_url = reverse("campaign_user_like")
        user_like = self.client.get(path=user_like_url, headers={
            "Authorization": token})
        self.assertAlmostEqual(1, (len(user_like.data)))
