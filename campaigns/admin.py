from django.contrib import admin
from django.utils.safestring import mark_safe
from campaigns.models import (
    Campaign,
    CampaignComment,
    CampaignReview,
    Funding,
    Participant
)


@admin.register(Campaign)
class CampaignDisplay(admin.ModelAdmin):
    """
    작성자 : 최준영
    내용 : 캠페인 admin 페이지 등록 클래스입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.30
    """

    list_display = [
        "title",
        "user",
        "members",
        "image_tag",
        "status",
        "category",
        "is_funding",
        "campaign_start_date",
        "campaign_end_date",
        "tag_list",
    ]
    fields = [
        "title",
        "content",
        "user",
        "status",
        "category",
        "participant",
        "like",
        "members",
        "image",
        "is_funding",
        "campaign_start_date",
        "campaign_end_date",
        "activity_start_date",
        "activity_end_date",
        "tags",
    ]
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    list_filter = [
        "user",
        "is_funding",
        "status",
    ]
    search_fields = [
        "title",
        "user",
        "content",
    ]

    def image_tag(self, campaign):
        if campaign.image:
            return mark_safe(f'<img src="{campaign.image.url}" style="width:50px;" />')
        
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


@admin.register(Funding)
class FundingDisplay(admin.ModelAdmin):
    """
    작성자 : 최준영
    내용 : 펀딩 admin 페이지 등록 클래스입니다.
    최초 작성일 : 2023.06.07
    업데이트 일자 :
    """

    list_display = [
        "campaign",
        "goal",
        "amount",
        "approve_file",
        "created_at",
        "updated_at",
    ]
    fields = [
        "campaign",
        "goal",
        "amount",
        "approve_file",
    ]
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    list_filter = [
        "campaign",
    ]
    search_fields = [
        "campaign",
        "goal",
        "amount",
        "approve_file",
        "created_at",
        "updated_at",
    ]


@admin.register(CampaignReview)
class CampaignReviewDisplay(admin.ModelAdmin):
    """
    작성자 : 최준영
    내용 : 캠페인 리뷰 admin 페이지 등록 클래스입니다.
    최초 작성일 : 2023.06.08
    업데이트 일자 : 2023.06.16
    """

    list_display = [
        "user",
        "campaign",
        "image_tag",
        "title",
        "content",
        "created_at",
        "updated_at",
    ]
    fields = [
        "user",
        "campaign",
        "image",
        "title",
        "content",
    ]
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    list_filter = [
        "campaign",
    ]
    search_fields = [
        "user",
        "campaign",
        "title",
        "content",
    ]

    def image_tag(self, review):
        if review.image:
            return mark_safe(f'<img src="{review.image.url}" style="width:50px;" />')


@admin.register(CampaignComment)
class CampaignCommentDisplay(admin.ModelAdmin):
    """
    작성자 : 최준영
    내용 : 캠페인 댓글 admin 페이지 등록 클래스입니다.
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    """

    list_display = [
        "user",
        "campaign",
        "content",
        "created_at",
        "updated_at",
    ]
    fields = [
        "user",
        "campaign",
        "content",
    ]
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    list_filter = [
        "campaign",
    ]
    search_fields = [
        "user",
        "campaign",
        "content",
    ]


admin.site.register(Participant)
