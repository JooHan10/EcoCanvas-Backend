from django.db import models
from users.models import User
from django.urls import reverse
from config.models import BaseModel
from taggit.managers import TaggableManager


class Campaign(BaseModel):
    """
    작성자 : 최준영
    내용 : 캠페인 모델 클래스입니다.
    is_funding의 BooleanField로 펀딩 여부를 체크하고
    status의 ChoiceField로 캠페인의 진행 상태를 체크합니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.29
    """

    class Meta:
        db_table = "campaign"

    STATUS_CHOICES = (
        (0, "미승인"),
        (1, "캠페인 모집중"),
        (2, "캠페인 종료"),
        (3, "캠페인 실패"),
    )
    CATEGORY_CHOICES = (
        (0, "봉사"),
        (1, "교육"),
        (2, "투자"),
        (3, "이벤트"),
        (4, "환경운동"),
    )

    user = models.ForeignKey(User, verbose_name="작성자",
                             on_delete=models.CASCADE, related_name="campaigns")
    participant = models.ManyToManyField(
        User, verbose_name="참가자", related_name="participants", blank=True)
    like = models.ManyToManyField(
        User, verbose_name="좋아요", related_name="likes", blank=True)
    title = models.CharField("제목", max_length=50)
    content = models.TextField("내용")
    members = models.PositiveIntegerField("모집 인원")
    campaign_start_date = models.DateTimeField("캠페인 시작일")
    campaign_end_date = models.DateTimeField("캠페인 마감일")
    activity_start_date = models.DateTimeField("활동 시작일", blank=True, null=True)
    activity_end_date = models.DateTimeField("활동 마감일", blank=True, null=True)
    image = models.ImageField(
        "이미지", blank=True, null=True, upload_to="campaign/%Y/%m/")
    is_funding = models.BooleanField("펀딩여부", default=False)
    status = models.PositiveSmallIntegerField(
        "진행 상태", choices=STATUS_CHOICES, default=0)
    category = models.PositiveSmallIntegerField(
        "카테고리", choices=CATEGORY_CHOICES, default=0)
    tags = TaggableManager(blank=True)

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse("campaign_detail_view", kwargs={"campaign_id": self.id})


class CampaignReview(BaseModel):
    """
    작성자 : 최준영
    내용 : 캠페인 리뷰 모델입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.16
    """

    class Meta:
        db_table = "campaign_review"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews")
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="reviews")
    title = models.CharField("캠페인 리뷰 제목", max_length=50)
    content = models.TextField("캠페인 리뷰 내용")
    image = models.ImageField("캠페인 리뷰 이미지", blank=True,
                              null=True, upload_to="review/%Y/%m/")

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse("campaign_review_detail_view", kwargs={"review_id": self.id})


class CampaignComment(BaseModel):
    """
    작성자 : 최준영
    내용 : 캠페인 댓글 모델입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.08
    """

    class Meta:
        db_table = "campaign_comment"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments")
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField("캠페인 댓글 내용")

    def __str__(self):
        return str(self.content)

    def get_absolute_url(self):
        return reverse("campaign_comment_detail_view", kwargs={"comment_id": self.id})


class Funding(BaseModel):
    """
    작성자 : 최준영
    내용 : 캠페인 펀딩 모델입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.07
    """

    class Meta:
        db_table = "funding"

    campaign = models.OneToOneField(
        Campaign, on_delete=models.CASCADE, related_name="fundings"
    )
    goal = models.PositiveIntegerField("펀딩 목표 금액")
    amount = models.PositiveIntegerField("펀딩 현재 금액", default=0)
    approve_file = models.FileField(
        "펀딩 승인 파일", upload_to="funding/%Y/%m/", null=True, blank=True)

    def __str__(self):
        return str(self.goal)


class Participant(models.Model):
    '''
    작성자 : 장소은
    내용 : 캠페인 참가자에게 시작일 전 알림을 보내기 위한 모델
    작성일 : 2023.06.22
    '''

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="campaign_participant_user")
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="campaign_key")
    is_participated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.campaign.title}"
