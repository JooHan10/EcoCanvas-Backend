from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, F
from django.utils import timezone
from campaigns.models import (
    Campaign,
    CampaignComment,
    CampaignReview,
    Participant
)
from campaigns.serializers import (
    CampaignSerializer,
    CampaignCreateSerializer,
    CampaignReviewSerializer,
    CampaignReviewCreateSerializer,
    CampaignCommentSerializer,
    CampaignCommentCreateSerializer,
    FundingCreateSerializer,
)


class CampaignView(APIView):
    """
    작성자 : 최준영
    내용 : 캠페인 View 클래스 입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.19
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination

    def get(self, request):
        """
        Query parameter에 대해 페이지네이션이 적용된 캠페인 목록을 Response하는 함수입니다.
        Parameter : end, order
        """
        end = self.request.query_params.get("end", None)
        order = self.request.query_params.get("order", None)
        keyword = self.request.query_params.get("keyword", None)
        category = self.request.query_params.get("category", None)
        
        queryset = (
            Campaign.objects.select_related("user")
            .select_related("fundings")
            .prefetch_related("like")
            .prefetch_related("participant")
            .all()
        )

        if end == "N":
            queryset = queryset.filter(
                Q(status=1)
                & Q(campaign_start_date__lte=timezone.now())
                & Q(campaign_end_date__gte=timezone.now())
            )
        elif end == "Y":
            queryset = queryset.filter(status__gte=2)
        else:
            queryset = queryset.filter(status__gte=1)

        orders_dict = {
            "recent": queryset.order_by("-created_at"),
            "closing": queryset.order_by("campaign_end_date"),
            "popular": queryset.annotate(participant_count=Count("participant")).order_by("-participant_count"),
            "like": queryset.annotate(like_count=Count("like")).order_by("-like_count"),
            "amount": queryset.order_by("-fundings__amount"),
        }

        queryset = orders_dict[order]

        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(content__icontains=keyword)
            )

        if category:
            queryset = queryset.filter(category=category)

        serializer = CampaignSerializer(queryset, many=True)

        pagination_instance = self.pagination_class()
        total_count = queryset.count()
        pagination_instance.total_count = total_count
        paginated_data = pagination_instance.paginate_queryset(
            serializer.data, request)

        return pagination_instance.get_paginated_response(paginated_data)

    def post(self, request):
        """
        캠페인 POST요청 함수입니다.
        is_funding이 True라면 펀딩정보를 같이 POST하는 방식으로 모듈화 했습니다.
        """
        if request.data["is_funding"] == "false":
            return self.create_campaign(request)
        else:
            return self.create_campaign_with_funding(request)

    def create_campaign(self, request):
        """
        is_funding이 false라면 캠페인만 request로 받아
        시리얼라이저를 검증한 후, 저장합니다.
        """
        serializer = CampaignCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        response_data = {"message": "캠페인이 작성되었습니다.", "data": serializer.data}
        return Response(response_data, status=status.HTTP_201_CREATED)

    def create_campaign_with_funding(self, request):
        """
        is_funding이 True라면 캠페인과 펀딩 모두 request로 받아
        시리얼라이저로 동시에 검증한 후, 저장합니다.
        """
        campaign_serializer = CampaignCreateSerializer(data=request.data)
        funding_serializer = FundingCreateSerializer(data=request.data)

        campaign_serializer.is_valid(raise_exception=True)
        funding_serializer.is_valid(raise_exception=True)
        
        campaign = campaign_serializer.save(user=request.user)
        funding_serializer.validated_data["campaign"] = campaign
        funding_serializer.save()
        response_data = {
            "message": "캠페인이 작성되었습니다.",
            "data": [campaign_serializer.data, funding_serializer.data],
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
    

class TagFilterView(ListAPIView):
    """
    작성자: 최준영
    내용 : 같은 태그의 캠페인을 모아볼 수 있는 클래스입니다.
    작성일: 2023.06.30
    """

    serializer_class = CampaignSerializer

    def get_queryset(self):
        tag = self.request.query_params.get("name", None)
        
        queryset = Campaign.objects.filter(tags__name__in=[tag])
        
        return queryset
    

class CampaignDetailView(APIView):
    """
    작성자 : 최준영
    내용 : 캠페인 디테일 View 입니다.
    개별 캠페인 GET과 그 캠페인에 대한 PUT, DELETE 요청을 처리합니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.30
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, campaign_id):
        """
        campaing_id를 Parameter로 받아 해당하는 캠페인에 GET 요청을 보내는 함수입니다.
        """

        queryset = get_object_or_404(Campaign, id=campaign_id)
        serializer = CampaignSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, campaign_id):
        """
        캠페인 PUT 요청 함수입니다.
        is_funding이 True라면 펀딩정보를 같이 PUT하는 방식으로 모듈화 했습니다.
        """
        if request.data["is_funding"] == "false":
            return self.update_campaign(request, campaign_id)
        else:
            return self.update_campaign_with_funding(request, campaign_id)

    def update_campaign(self, request, campaign_id):
        """
        is_funding이 false라면 캠페인만 request로 받아
        시리얼라이저를 검증한 후, 저장합니다.
        """
        queryset = get_object_or_404(Campaign, id=campaign_id)
        if request.user == queryset.user:
            serializer = CampaignCreateSerializer(
                queryset, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "캠페인이 수정되었습니다.", "data": serializer.data},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "캠페인 수정에 실패했습니다.", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"message": "해당 캠페인을 수정할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

    def update_campaign_with_funding(self, request, campaign_id):
        """
        is_funding이 True라면 캠페인과 펀딩 모두 request로 받아
        시리얼라이저로 동시에 검증한 후, 저장합니다.
        """
        queryset = get_object_or_404(Campaign, id=campaign_id)
        if request.user == queryset.user:
            campaign_serializer = CampaignCreateSerializer(queryset, data=request.data, partial=True)
            funding_serializer = FundingCreateSerializer(data=request.data, partial=True)

            campaign_serializer.is_valid(raise_exception=True)
            funding_serializer.is_valid(raise_exception=True)

            campaign = campaign_serializer.save()
            funding_serializer.validated_data["campaign"] = campaign
            funding_serializer.save()
            response_data = {
                "message": "캠페인이 수정되었습니다.",
                "data": [campaign_serializer.data, funding_serializer.data],
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "해당 캠페인을 수정할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

    def delete(self, request, campaign_id):
        """
        campaing_id를 Parameter로 받아 해당하는 캠페인을 삭제할 수 있는
        DELETE 요청 함수입니다.
        """
        queryset = get_object_or_404(Campaign, id=campaign_id)
        if request.user == queryset.user:
            queryset.delete()
            return Response(
                {"message": "캠페인이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "해당 캠페인을 삭제할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )


class CampaignLikeView(APIView):
    """
    작성자 : 최준영
    내용 : 캠페인 좋아요 View 입니다.
    캠페인에 대한 좋아요 POST 요청을 처리합니다.
    최초 작성일 : 2023.06.09
    업데이트 일자 : 2023.06.15
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, campaign_id):
        queryset = get_object_or_404(Campaign, id=campaign_id)
        is_liked = queryset.like.filter(id=request.user.id).exists()
        return Response({"is_liked": is_liked}, status=status.HTTP_200_OK)

    def post(self, request, campaign_id):
        queryset = get_object_or_404(Campaign, id=campaign_id)
        if queryset.like.filter(id=request.user.id).exists():
            queryset.like.remove(request.user)
            is_liked = False
            message = "좋아요 취소!"
        else:
            queryset.like.add(request.user)
            is_liked = True
            message = "좋아요 성공!"

        return Response({"is_liked": is_liked, "message": message}, status=status.HTTP_200_OK)


class CampaignParticipationView(APIView):
    """
    작성자 : 최준영
    내용 : 캠페인 유저 참가 View 입니다.
    캠페인에 대한 참가 POST 요청을 처리합니다.
    최초 작성일 : 2023.06.11
    업데이트 일자 : 2023.07.02
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, campaign_id):
        queryset = get_object_or_404(Campaign, id=campaign_id)
        is_participated = queryset.participant.filter(
            id=request.user.id).exists()
        return Response({"is_participated": is_participated}, status=status.HTTP_200_OK)

    def post(self, request, campaign_id):
        queryset = get_object_or_404(Campaign, id=campaign_id)

        participant_count = queryset.participant.count()
        members = queryset.members

        if queryset.participant.filter(id=request.user.id).exists():
            queryset.participant.remove(request.user)
            is_participated = False
            message = "캠페인 참가 취소!"
            participant = Participant.objects.get(
                campaign=queryset,
                user=request.user
            )
            participant.delete()

        else:
            if participant_count + 1 > members:
                return Response(
                {"message": "캠페인 참가 정원을 초과하여 신청할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
            else:
                queryset.participant.add(request.user)
                is_participated = True
                message = "캠페인 참가 성공!"

                participant = Participant.objects.create(
                    user=request.user,
                    campaign=queryset,
                    is_participated=True
                )
                participant.save()

        return Response({"is_participated": is_participated, "message": message}, status=status.HTTP_200_OK)


class CampaignStatusChecker():
    """
    작성자 : 최준영
    내용 : scheduler를 통해 관리할 캠페인 함수 클래스입니다.
    최초 작성일 : 2023.06.08
    업데이트 일자 : 2023.06.30
    """
    def check_campaign_status():
        """
        status가 1인 캠페인 중 완료 날짜가 되거나 지난 캠페인의 
        status를 2로 바꿉니다.
        """
        now = timezone.now()
        campaigns = Campaign.objects.filter(status=1)

        for campaign in campaigns:
            if campaign.campaign_end_date <= now:
                campaign.status = 2
                campaign.save()

    def check_funding_success():
        """
        종료된 캠페인의 펀딩 성공여부를 판단해 펀딩에 실패한 캠페인의 
        status를 3으로 바꿉니다.
        """
        now = timezone.now()
        campaigns = Campaign.objects.filter(status=2).filter(fundings__amount__lt=F("fundings__goal"))

        for campaign in campaigns:
            campaign.status = 3
            campaign.save()


class ReviewCommentPagination(PageNumberPagination):
    """
    작성자: 최준영
    내용 : 리뷰, 댓글 페이지네이션 클래스입니다.
    작성일: 2023.06.25
    """
    page_size = 5
    page_size_query_param = "page_size"


class CampaignReviewView(APIView):
    """
    작성자 : 최준영
    내용 : 캠페인 리뷰 View 입니다.
    완료가 된 캠페인의 리뷰에 대한 GET, POST, PUT, DELETE 요청을 처리합니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.29
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = ReviewCommentPagination

    def get(self, request, campaign_id):
        """
        캠페인 리뷰를 볼 수 있는 GET 요청 함수입니다.
        """
        queryset = get_object_or_404(Campaign, id=campaign_id)
        review = queryset.reviews.all()
        serializer = CampaignReviewSerializer(review, many=True)

        pagination_instance = self.pagination_class()
        paginated_data = pagination_instance.paginate_queryset(
            serializer.data, request)

        return pagination_instance.get_paginated_response(paginated_data)

    def post(self, request, campaign_id):
        """
        캠페인 리뷰를 작성하는 Post 요청 함수입니다.
        """
        serializer = CampaignReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, campaign_id=campaign_id)
        return Response(
            {"message": "리뷰가 작성되었습니다.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def put(self, request, review_id):
        """
        리뷰를 수정할 수 있는 PUT 요청 함수입니다.
        """
        queryset = get_object_or_404(CampaignReview, id=review_id)
        if request.user == queryset.user:
            serializer = CampaignReviewCreateSerializer(
                queryset, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "리뷰가 수정되었습니다.", "data": serializer.data},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "리뷰 수정에 실패했습니다.", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"message": "해당 리뷰를 수정할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

    def delete(self, request, review_id):
        """
        리뷰를 삭제할 수 있는 DELETE 요청 함수입니다.
        """
        queryset = get_object_or_404(CampaignReview, id=review_id)
        if request.user == queryset.user:
            queryset.delete()
            return Response(
                {"message": "리뷰가 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "해당 리뷰를 삭제할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )


class CampaignCommentView(APIView):
    """
    작성자 : 최준영
    내용 : 캠페인 댓글 View 입니다.
    캠페인의 댓글에 대한 GET, POST, PUT, DELETE 요청을 처리합니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.29
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = ReviewCommentPagination

    def get(self, request, campaign_id):
        """
        캠페인 댓글을 볼 수 있는 GET 요청 함수입니다.
        """
        queryset = get_object_or_404(Campaign, id=campaign_id)
        comment = queryset.comments.all()
        serializer = CampaignCommentSerializer(comment, many=True)

        pagination_instance = self.pagination_class()
        paginated_data = pagination_instance.paginate_queryset(
            serializer.data, request)

        return pagination_instance.get_paginated_response(paginated_data)

    def post(self, request, campaign_id):
        """
        캠페인 댓글을 작성하는 Post 요청 함수입니다.
        """
        serializer = CampaignCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, campaign_id=campaign_id)
        return Response(
            {"message": "댓글이 작성되었습니다.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def put(self, request, comment_id):
        """
        댓글을 수정할 수 있는 PUT 요청 함수입니다.
        """
        queryset = get_object_or_404(CampaignComment, id=comment_id)
        if request.user == queryset.user:
            serializer = CampaignCommentCreateSerializer(
                queryset, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "댓글 수정완료", "data": serializer.data},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "댓글 수정에 실패했습니다.", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"message": "해당 댓글을 수정할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

    def delete(self, request, comment_id):
        """
        댓글을 삭제할 수 있는 DELETE 요청 함수입니다.
        """
        queryset = get_object_or_404(CampaignComment, id=comment_id)
        if request.user == queryset.user:
            queryset.delete()
            return Response(
                {"message": "댓글이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"message": "해당 댓글을 삭제할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )


class ParticipatingCampaignView(APIView):
    """
    작성자 : 박지홍
    내용 : 유저가 작성한 캠페인을 보여주는 기능.
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        campaign = Campaign.objects.filter(user=request.user)
        serializer = CampaignSerializer(campaign, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CampaignUserReviewView(APIView):
    """
    작성자 : 박지홍
    내용 : 유저가 작성한 리뷰를 보여주는 기능
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        review = CampaignReview.objects.filter(user=request.user)
        serializer = CampaignReviewSerializer(review, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CampaignUserLikeView(APIView):
    """
    작성자 : 박지홍
    내용 : 유저가 좋아요 누른 캠페인을 보여주는 기능.
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        review = Campaign.objects.filter(like=request.user)
        serializer = CampaignSerializer(review, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CampaignUserCommentView(APIView):
    """
    작성자 : 박지홍
    내용 : 유저가 작성한 댓글을 보여주는 기능.
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        review = CampaignComment.objects.filter(
            user=request.user).select_related("campaign")
        serializer = CampaignCommentSerializer(review, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyAttendCampaignView(APIView):
    """
    작성자 : 장소은
    내용 : 유저가 참여한 캠페인을 보여주는 기능.
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        mycampaigns = Campaign.objects.filter(
            participant=request.user).order_by('-activity_end_date')
        serializer = CampaignSerializer(mycampaigns, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CampaignStatusUpdateAPIView(APIView):
    '''
    작성자: 장소은
    내용: 백오피스에서 신청내역의 캠페인의 상태값만 수정
          별도의 시리얼라이저나 응답데이터가 필요X
    작성일: 2023.06.17
    '''

    def put(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        campaign.status = request.data.get('status')
        campaign.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CampaiginApplyListView(APIView):
    '''
    작성자: 장소은
    내용: 백오피스에서 캠페인 모든 신청내역 조회
    작성일: 2023.06.19
    '''
    class MyPagination(PageNumberPagination):
        page_size = 10
        page_query_param = 'page'
        max_page_size = 50

    pagination_class = MyPagination

    def get(self, request):
        campaigns = Campaign.objects.all()
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(campaigns, request)
        serializer = CampaignSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)
