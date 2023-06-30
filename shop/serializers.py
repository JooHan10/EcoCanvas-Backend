from rest_framework.serializers import ValidationError
from rest_framework import serializers
from .models import ShopProduct, ShopCategory, ShopImageFile, ShopOrder, ShopOrderDetail, RestockNotification
import re


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopImageFile
        fields = ['id', 'product', 'image_file']


class ProductListSerializer(serializers.ModelSerializer):
    '''
    작성자:장소은
    내용: 카테고리별 상품목록 조회/다중 이미지 업로드 시 필요한 Serializer 클래스
    작성일: 2023.06.07
    업데이트일: 2023.06.21
    '''
    images = PostImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(child=serializers.ImageField(
        max_length=1000000, allow_empty_file=False, use_url=False), write_only=True
    )
    category_name = serializers.CharField(
        source="category.category_name", read_only=True)
    sold_stock = serializers.SerializerMethodField()

    class Meta:
        model = ShopProduct
        fields = ['id', 'product_name', 'product_price', 'product_stock',
                        'product_desc', 'product_date', 'category', 'images', 'uploaded_images', 'hits', 'category_name', 'sold_out', 'sold_stock']

    def get_sold_stock(self, obj):
        return obj.product_stock - obj.product_set.filter(order_detail_status=0).count()

    def get(self, instance):
        request = self.context.get('request')

        if instance.sold_out and not request.user.is_amdin:
            raise serializers.ValidationError('해당 상품은 현재 품절되었습니다.')

        return super().get(instance)

    def validate_product_price(self, value):
        try:
            price = value
            if price <= 0:
                raise serializers.ValidationError(
                    '상품 가격은 양의 실수이어야 합니다.')
        except ValueError:
            raise serializers.ValidationError('상품 가격은 숫자여야 합니다.')

        return price

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        product_stock = validated_data.get('product_stock', None)

        if product_stock is not None and product_stock < 0:
            raise serializers.ValidationError('상품 재고는 음수일 수 없습니다.')
        product = super().create(validated_data)

        for images in uploaded_images:
            ShopImageFile.objects.create(image_file=images, product=product)

        return product

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        product_stock = validated_data.get('product_stock', None)

        if product_stock is not None and product_stock < 0:
            raise serializers.ValidationError('상품 재고는 음수일 수 없습니다.')
        images = instance.images.all()

        for i, image in enumerate(uploaded_images):
            if i < len(images):
                images[i].image_file = image
                images[i].save()
            else:
                ShopImageFile.objects.create(
                    image_file=image, product=instance)

        return super().update(instance, validated_data)


class CategoryListSerializer(serializers.ModelSerializer):
    '''
    작성자:박지홍
    내용: 카테고리별 조회시 필요한 Serializer 클래스
    작성일: 2023.06.09
    '''
    class Meta:
        model = ShopCategory
        fields = '__all__'


class OrderDetailSerializer(serializers.ModelSerializer):
    '''
    작성자:장소은
    내용: 주문 상세 정보에 관련해서 필요한 시리얼라이저
    작성일 : 2023.06.13
    '''
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_order_detail_status_display()

    class Meta:
        model = ShopOrderDetail
        fields = ['order', 'status', 'product_count', 'product']


class OrderProductSerializer(serializers.ModelSerializer):
    '''
    작성자:장소은
    내용: 1. 사용자가 주문 생성 시 주문에 대한 정보도 같이 저장됩니다. 
          2. 주문한 수량만큼 해당 상품의 재고를 출고시킵니다.
          3. 사용자가 해당 상품에 대한 주문 목록들을 볼 수 있습니다.
          4. 주문한 수량이 재고보다 클 시 ValdationError 발생(업뎃)  
    작성일 : 2023.06.13
    업데이트일 : 2023.06.27
    '''
    order_info = OrderDetailSerializer(
        many=True, read_only=True)
    order_date = serializers.SerializerMethodField()
    order_quantity = serializers.IntegerField(write_only=True)
    product = serializers.IntegerField(write_only=True)

    class Meta:
        model = ShopOrder
        fields = ['id', 'order_info', 'order_quantity', 'order_date', 'zip_code', 'address',
                  'address_detail', 'address_message', 'receiver_name', 'receiver_number', 'user',  'order_totalprice', 'product']

    def get_order_date(self, obj):
        return obj.order_date.strftime("%Y년 %m월 %d일 %R")

    def validate_order_quantity(self, order_quantity):
        if order_quantity <= 0:
            raise serializers.ValidationError("주문 수량은 0보다 작을 수 없습니다.")
        return order_quantity

    def validate_receiver_number(self, receiver_number):
        if not re.match(r'^\d{3}-\d{3,4}-\d{4}$', receiver_number):
            raise serializers.ValidationError(
                "유효한 연락처를 입력해주세요! 예시: 010-1234-5678")
        return receiver_number

    def get_product_instance(self, product_key):
        try:
            return ShopProduct.objects.get(id=product_key.id)
        except ShopProduct.DoesNotExist:
            raise serializers.ValidationError("유효한 상품을 선택해주세요.")

    def update_product_stock(self, product, order_quantity):
        product.product_stock -= order_quantity
        if product.product_stock == 0:
            product.sold_out = True
            product.restock_available = True
            product.restocked = False
        product.save()

    def create_order_detail(self, order, product, order_quantity):
        order_info = ShopOrderDetail(
            order=order,
            product=product,
            product_count=order_quantity,
            order_detail_status=0
        )
        order_info.save()

    def create(self, validated_data):
        order_quantity = validated_data.pop('order_quantity', [])
        product_key = validated_data.pop('product', [])
        order_quantity = self.validate_order_quantity(order_quantity)
        receiver_number = self.validate_receiver_number(
            validated_data.get('receiver_number'))

        product = self.get_product_instance(product_key)
        self.validate_product_stock(product, order_quantity)  # 재고 유효성 검사
        self.update_product_stock(product, order_quantity)

        order = ShopOrder.objects.create(**validated_data)
        self.create_order_detail(order, product, order_quantity)

        return order

    def validate_product_stock(self, product, order_quantity):
        if product.product_stock < order_quantity:
            raise serializers.ValidationError(
                f"{product}의 상품 재고가 주문 수량보다 적습니다.")


class RestockNotificationSerializer(serializers.ModelSerializer):
    '''
    작성자 : 장소은
    내용 : 재입고 알림 조회를 위한 시리얼라이저
    작성일 : 2023.06.22
    '''
    class Meta:
        model = RestockNotification
        fields = ['id', 'message', 'created_at',
                  'product', 'notification_sent']
