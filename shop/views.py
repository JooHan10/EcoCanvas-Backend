from rest_framework.generics import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import (
    ShopProduct,
    ShopCategory,
    ShopOrder,
    ShopOrderDetail,
    RestockNotification
)
from .serializers import (
    ProductListSerializer,
    CategoryListSerializer,
    OrderProductSerializer,
    OrderListSerializer,
    OrderDetailSerializer
)
from config.permissions import IsAdminUserOrReadonly
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from django.core.cache import cache
from django.db import transaction
from django.db import IntegrityError


class CustomPagination(PageNumberPagination):
    '''
    작성자: 장소은
    내용 : 페이지네이션을 위한 커스텀페이지네이션
    작성일: 2023.06.16
    '''
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 60


class ProductListViewAPI(APIView):
    '''
    작성자:장소은
    내용: 전체 상품 목록 쿼리 매개변수 통해 조건별 정렬 및 검색 조회 API
    작성일: 2023.06.16
    업데이트 일: 2023.06.20
    '''
    pagination_class = CustomPagination

    def get(self, request):
        sort_by = request.GET.get('sort_by')
        search_query = request.GET.get('search_query')

        products = ShopProduct.objects.all()

        # 정렬 처리
        if sort_by == 'hits':
            products = ShopProduct.objects.all().order_by('-hits')
        elif sort_by == 'latest':
            products = ShopProduct.objects.all().order_by('-product_date')
        elif sort_by == 'high_price':
            products = ShopProduct.objects.all().order_by('-product_price')
        elif sort_by == 'low_price':
            products = ShopProduct.objects.all().order_by('product_price')

        # 검색 처리
        if search_query:
            products = products.filter(
                Q(product_name__icontains=search_query) |
                Q(product_desc__icontains=search_query)
            )

        # 페이지네이션 처리
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)


class ProductCategoryListViewAPI(APIView):
    '''
    작성자:장소은
    내용: 카테고리별 상품목록 정렬 및 검색 조회(조회순/높은금액/낮은금액/최신순) (일반,관리자) / 상품 등록(관리자)
    작성일: 2023.06.06
    업데이트일: 2023.06.120
    '''
    permission_classes = [IsAdminUserOrReadonly]
    pagination_class = CustomPagination

    def get(self, request, category_id):
        category = get_object_or_404(ShopCategory, id=category_id)

        sort_by = request.GET.get('sort_by')
        search_query = request.GET.get('search_query')

        products = ShopProduct.objects.filter(category_id=category.id)

        # 정렬 처리
        if sort_by == 'hits':
            products = ShopProduct.objects.filter(
                category_id=category.id).order_by('-hits')
        elif sort_by == 'high_price':
            products = ShopProduct.objects.filter(
                category_id=category.id).order_by('-product_price')
        elif sort_by == 'low_price':
            products = ShopProduct.objects.filter(
                category_id=category.id).order_by('product_price')
        else:
            products = ShopProduct.objects.filter(
                category_id=category.id).order_by('-product_date')

        # 검색 처리
        if search_query:
            products = products.filter(
                Q(product_name__icontains=search_query) |
                Q(product_desc__icontains=search_query)
            )

        # 페이지네이션 처리
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    def post(self, request, category_id):
        category = get_object_or_404(ShopCategory, id=category_id)
        serializer = ProductListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(category=category)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailViewAPI(APIView):
    '''
    작성자:장소은
    내용: 카테고리별 상품 상세 조회/ 수정 / 삭제 (일반유저는 조회만)
        세션과 쿠키를 이용하여 조회수 중복방지
    작성일: 2023.06.06
    업데이트일: 2023.06.29
    '''
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, product_id):
        product = get_object_or_404(ShopProduct, id=product_id)

        session_key = request.session.session_key
        viewed_products = cache.get(f"viewed_products_{session_key}", set())

        if product_id not in viewed_products:
            product.hits += 1
            product.save()

        viewed_products.add(product_id)
        cache.set(f"viewed_products_{session_key}",
                  viewed_products, timeout=86400)

        serializer = ProductListSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, product_id):
        if not request.user.is_admin:
            return Response({"message": "관리자만 수정할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        product = get_object_or_404(ShopProduct, id=product_id)
        serializer = ProductListSerializer(
            product, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, product_id):
        if not request.user.is_admin:
            return Response({"message": "관리자만 수정할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        product = get_object_or_404(ShopProduct, id=product_id)
        product.delete()
        return Response({"massage": "삭제 완료"}, status=status.HTTP_204_NO_CONTENT)


class AdminProductViewAPI(APIView):
    '''
    작성자 : 박지홍
    내용 : 어드민 페이지에서 전체 상품 목록을 받아오기위해 사용
    최초 작성일 : 2023.06.09
    업데이트 일자 :
    '''
    pagination_class = CustomPagination
    permission_classes = [IsAdminUserOrReadonly]

    def get(self, request):
        products = ShopProduct.objects.all().order_by('-product_date')
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)


class AdminCategoryViewAPI(APIView):
    '''
    작성자 : 박지홍
    내용 : 어드민 페이지에서 전체 카테고리 목록을 받아오기위해 사용
    최초 작성일 : 2023.06.09
    업데이트 일자 :
    '''
    permission_classes = [IsAdminUserOrReadonly]

    def get(self, request):
        categorys = ShopCategory.objects.all()
        serializer = CategoryListSerializer(categorys, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CategoryListSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"message": "이미 존재하는 카테고리 이름입니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderProductViewAPI(APIView):
    '''
    작성자 : 장소은
    내용 : 해당 상품에 대한 주문 생성(+다중 주문), 트랜잭션을 이용하여 모든 주문이 유효성 검사를 통과해야 db저장 되도록 개선
    최초 작성일 : 2023.06.13
    업데이트일 : 2023.06.30
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_detail_data = request.data.get('product', [])
        order_data = request.data.get('order', [])
        order_data['user'] = request.user.id
        valid_orders = []
        order_serializer = OrderProductSerializer(data=order_data)

        if order_serializer.is_valid():
            order = order_serializer.save()
            with transaction.atomic():
                for _data in order_detail_data:
                    product_id = _data.get('product')
                    _data['order'] = order.id
                    product = get_object_or_404(ShopProduct, id=product_id)
                    serializer = OrderDetailSerializer(data=_data)
                    if serializer.is_valid():
                        valid_orders.append((serializer, product))
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                order_list = []
                for serializer, product in valid_orders:
                    serializer.save(product=product)
                    order_list.append(serializer.data)

                return Response(order_list, status=status.HTTP_201_CREATED)
        else:
            return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminOrderViewAPI(APIView):
    '''
    작성자 : 장소은
    내용 : 어드민 페이지에서 상품 모든 주문내역 조회
    최초 작성일 : 2023.06.09
    업데이트 일자 :
    '''
    pagination_class = CustomPagination
    permission_classes = [IsAdminUser]

    def get(self, request):
        orders = ShopOrder.objects.all().order_by('-order_date')
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(orders, request)
        serializer = OrderListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MypageOrderViewAPI(APIView):
    '''
    작성자 : 장소은
    내용 : 마이페이지에서 유저의 모든 주문내역 조회, 페이지네이션
    최초 작성일 : 2023.06.14
    업데이트 일자 : 2023.06.18
    '''
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request):
        orders = ShopOrder.objects.filter(
            user=request.user.id).order_by('-order_date')
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(orders, request)
        serializer = OrderListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class RestockNotificationViewAPI(APIView):
    '''
    작성자: 장소은
    내용: 재입고 알림 신청
    작성일: 2023.06.20
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        product = get_object_or_404(ShopProduct, id=product_id)
        user = request.user
        if product.sold_out:
            if not RestockNotification.objects.filter(product=product, user=user).exists():
                RestockNotification.objects.create(product=product, user=user)
                return Response({"message": "재입고 알림 신청이 완료되었습니다."}, status=status.HTTP_201_CREATED)
            return Response({"message": "이미 재입고 알림을 구독 하셨습니다."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "상품이 품절되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)


class HandleOrderStatusViewAPI(APIView):
    '''
    작성자 : 장소은
    내용 : 작성자 페이지에서 상품 주문건의 상태 변경
    작성일 : 2023.07.01
    '''
    permission_classes = [IsAdminUser]

    def put(self, request, order_id):
        order = get_object_or_404(ShopOrderDetail, id=order_id)
        order.order_detail_status = request.data.get('status')

        order.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminCategoryUpdateViewAPI(APIView):
    '''
    작성자 : 장소은
    내용 : 어드민 페이지에서 카테고리 수정, 삭제
    작성일 : 2023.07.02
    '''
    permission_classes = [IsAdminUser]

    def put(self, request, category_id):
        category = get_object_or_404(ShopCategory, id=category_id)
        serializer = CategoryListSerializer(category, data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except IntegrityError:
                return Response(
                    {"message": "이미 존재하는 카테고리 이름입니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, category_id):
        category = get_object_or_404(ShopCategory, id=category_id)
        category.delete()
        return Response({"message": "삭제 완료"}, status=status.HTTP_204_NO_CONTENT)


class SendRefundViewAPI(APIView):
    '''
        작성자 : 송지명
        작성일 : 2023.07.04
        작성내용 : 어드민 페이지에서 취소 요청 받은 데이터 필터.  
        업데이트 날짜 : 
        '''
    pagination_class = CustomPagination
    permission_classes = [IsAdminUser]

    def get(self, request):

        order_details = ShopOrderDetail.objects.filter(
            order_detail_status=6).order_by('-order__order_date')
        orders = [order_detail.order for order_detail in order_details]
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(orders, request)
        serializer = OrderProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
