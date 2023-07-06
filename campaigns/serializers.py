from rest_framework import serializers
from campaigns.models import (
    Campaign,
    CampaignReview,
    CampaignComment,
    Funding,
)
from users.models import UserProfile
from users.serializers import UserProfileSerializer
from taggit.serializers import (TagListSerializerField,
                                TaggitSerializer)


class FundingSerializer(serializers.ModelSerializer):
    """
    작성자 : 최준영
    내용 : 펀딩 시리얼라이저 입니다.
    최초 작성일 : 2023.06.07
    업데이트 일자 :
    """

    class Meta:
        model = Funding
        fields = "__all__"


class FundingCreateSerializer(serializers.ModelSerializer):
    """
    작성자 : 최준영
    내용 : 펀딩 생성 시리얼라이저 입니다.
    최초 작성일 : 2023.06.07
    업데이트 일자 : 2023.06.20
    """

    class Meta:
        model = Funding
        fields = (
            "goal",
            "amount",
            "approve_file",
        )


class CampaignSerializer(serializers.ModelSerializer):
    """
    작성자 : 최준영
    내용 : 캠페인 디테일 시리얼라이저 입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.30
    """

    tags = TagListSerializerField()
    user = serializers.SerializerMethodField()
    fundings = FundingSerializer()
    like_count = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = (
            "id",
            "user",
            "user_id",
            "title",
            "content",
            "members",
            "is_funding",
            "image",
            "category",
            "tags",
            "status",
            "fundings",
            "campaign_start_date",
            "campaign_end_date",
            "activity_start_date",
            "activity_end_date",
            "like_count",
            "participant_count",
        )

    def get_user(self, obj):
        return obj.user.username

    def get_user_id(self, obj):
        return obj.user.id

    def get_like_count(self, obj):
        return obj.like.count()

    def get_participant_count(self, obj):
        return obj.participant.count()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_category(self, obj):
        return obj.get_category_display()
    

class CampaignListSerializer(serializers.ModelSerializer):
    """
    작성자 : 최준영
    내용 : 캠페인 리스트 시리얼라이저 입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.30
    """
    user = serializers.SerializerMethodField()
    fundings = FundingSerializer()
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = (
            "id",
            "user",
            "title",
            "members",
            "image",
            "status",
            "fundings",
            "campaign_start_date",
            "campaign_end_date",
            "participant_count",
        )

    def get_user(self, obj):
        return obj.user.username

    def get_participant_count(self, obj):
        return obj.participant.count()


class CampaignCreateSerializer(TaggitSerializer, serializers.ModelSerializer):
    """
    작성자 : 최준영
    내용 : 캠페인 생성 시리얼라이저 입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.30
    """

    campaign_start_date = serializers.DateTimeField()
    campaign_end_date = serializers.DateTimeField()
    activity_start_date = serializers.DateTimeField(
        required=False, allow_null=True)
    activity_end_date = serializers.DateTimeField(
        required=False, allow_null=True)
    tags = TagListSerializerField()

    class Meta:
        model = Campaign
        fields = (
            "title",
            "content",
            "members",
            "campaign_start_date",
            "campaign_end_date",
            "activity_start_date",
            "activity_end_date",
            "image",
            "is_funding",
            "status",
            "category",
            "tags",
        )

    def validate(self, data):
        """
        캠페인 validation 함수입니다.
        """
        data = super().validate(data)
        data = self.validate_date(data)

        return data

    def validate_date(self, data):
        """
        캠페인 시작일이 마감일보다 늦는지 확인합니다.
        캠페인 활동 시작일만 있는지, 마감일만 있는지 또 시작일이 마감이보다 늦는지 확인합니다.
        """
        if data["campaign_start_date"] >= data["campaign_end_date"]:
            raise serializers.ValidationError(
                detail={"campaign_start_date": "캠페인 시작일은 마감일보다 이전일 수 없습니다."}
            )

        activity_start_date = data.get("activity_start_date")
        activity_end_date = data.get("activity_end_date")

        if activity_start_date and not activity_end_date:
            raise serializers.ValidationError(
                detail={"activity_end_date": "활동 종료일은 필수입니다."}
            )

        if not activity_start_date and activity_end_date:
            raise serializers.ValidationError(
                detail={"activity_start_date": "활동 시작일은 필수입니다."}
            )

        if activity_start_date and activity_end_date:
            if activity_start_date > activity_end_date:
                raise serializers.ValidationError(
                    detail={"activity_start_date": "활동 시작일은 마감일보다 이전일 수 없습니다."}
                )

        return data


class CampaignReviewSerializer(serializers.ModelSerializer):
    """
    작성자 : 최준영
    내용 : 캠페인 후기 시리얼라이저 입니다.
          +) author필드 추가 
    최초 작성일 : 2023.06.06
    업데이트 일자 :2023.06.16
    """

    author = serializers.CharField(source="user.username", read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = CampaignReview
        fields = "__all__"

    def get_user(self, obj):
        return obj.user.username


class CampaignReviewCreateSerializer(serializers.ModelSerializer):
    """
    작성자 : 최준영
    내용 : 캠페인 후기 생성 시리얼라이저 입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 :2023.06.16
    """

    class Meta:
        model = CampaignReview
        fields = (
            "title",
            "content",
            "image"
        )


class CampaignCommentSerializer(serializers.ModelSerializer):
    """
    작성자 : 최준영
    내용 : 캠페인 댓글 시리얼라이저 입니다.
          +) author필드 추가 
    최초 작성일 : 2023.06.06
    업데이트 일자 :2023.06.14
    """

    author = serializers.CharField(source="user.username", read_only=True)
    campaign_title = serializers.CharField(
        source="campaign.title", read_only=True)
    user = serializers.SerializerMethodField()
    user_image = serializers.SerializerMethodField()

    class Meta:
        model = CampaignComment
        fields = (
            "author",
            "campaign",
            "campaign_title",
            "content",
            "created_at",
            "id",
            "user",
            "user_id",
            "user_image",
        )

    def get_user(self, obj):
        return obj.user.username

    def get_user_id(self, obj):
        return obj.user.id

    def get_user_image(self, obj):
        user_id = obj.user.id
        user_profile = UserProfile.objects.filter(user_id=user_id).first()
        if user_profile and user_profile.image:
            user_profile_serializer = UserProfileSerializer(user_profile)
            return user_profile_serializer.data["image"]
        else:
            return None


class CampaignCommentCreateSerializer(serializers.ModelSerializer):
    """
    작성자 : 최준영
    내용 : 캠페인 댓글 생성 시리얼라이저 입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 :
    """

    class Meta:
        model = CampaignComment
        fields = ("content",)


class MyCampaingSerializer(serializers.ModelSerializer):
    """
    작성자 : 장소은
    내용 : 캠페인 참가/신청 내역 조회를 위한 시리얼라이저 입니다.
    최초 작성일 : 2023.07.05
    """
    status = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = ("id", "title", "content", "campaign_end_date",
                  "activity_start_date", "activity_end_date", "image", "status")

    def get_status(self, obj):
        return obj.get_status_display()
