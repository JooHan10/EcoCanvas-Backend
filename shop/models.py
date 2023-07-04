from django.db import models
from users.models import User
from django.urls import reverse


class ShopCategory(models.Model):
    '''
    작성자 : 장소은
    내용 : 상품 분류 카테고리 모델
    최초 작성일: 2023.06.06
    업데이트 일자:
    '''
    category_name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return str(self.category_name)

    def get_absolute_url(self):
        return reverse('product_view', kwargs={"category_id": self.id})


class ShopProduct(models.Model):
    '''
    작성자 : 장소은
    내용 : 상품의 정보(이름,가격,수량,설명,등록일)를 나타내는 모델, 품절처리,재입고 플래그 추가 
    최초 작성일: 2023.06.06
    업데이트 일자:2023.06.20
    '''
    product_name = models.CharField(max_length=30)
    product_price = models.PositiveIntegerField(default=0)
    product_stock = models.PositiveIntegerField(default=0)
    product_desc = models.TextField()
    product_date = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        ShopCategory, on_delete=models.CASCADE, related_name='products')
    hits = models.PositiveIntegerField(default=0)
    sold_out = models.BooleanField(default=False)
    restock_available = models.BooleanField(default=False)
    restocked = models.BooleanField(default=False)

    # 상품의 초기 입고 후 재고가 0이 되었을 경우 품절 처리
    def save(self, *args, **kwargs):
        if self.product_stock == 0:
            self.sold_out = True
            self.restock_available = True
            self.restocked = False

        else:  # 상품이 초기 입고가 아닌 재입고일 경우
            if self.product_stock > 0 and self.restock_available == True:
                self.sold_out = False
                self.restock_available = False
                self.restocked = True
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.product_name)

    def get_absolute_url(self):
        return reverse("campaign_review_detail_view", kwargs={"review_id": self.id})


class ShopOrder(models.Model):
    '''
    작성자 : 장소은
    내용 : 주문 정보를 나타내는 모델
    최초 작성일: 2023.06.06
    업데이트 일자:2023.06.23
    '''
    order_totalprice = models.PositiveIntegerField(default=0)
    order_date = models.DateTimeField(auto_now_add=True)
    zip_code = models.CharField(max_length=20)
    address = models.CharField(max_length=100)
    address_detail = models.CharField(max_length=100)
    address_message = models.CharField(max_length=150)
    receiver_name = models.CharField(max_length=20)
    receiver_number = models.CharField(max_length=20)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class ShopOrderDetail(models.Model):
    '''
    작성자 : 장소은
    내용 : 주문의 상태를 나타내는 모델
    최초 작성일: 2023.06.06
    업데이트 일자:
    '''
    product_count = models.PositiveIntegerField(default=0)
    STATUS_CHOICES = (
        (0, "주문 접수 완료"),
        (1, "주문취소"),
        (2, "배송 준비 완료"),
        (3, "배송 시작"),
        (4, "배송 중"),
        (5, "배송 완료"),
        (6, "주문취소 요청")
    )
    order = models.ForeignKey(
        ShopOrder, on_delete=models.CASCADE, related_name='order_info')
    product = models.ForeignKey(
        ShopProduct, on_delete=models.CASCADE, related_name='product_set')
    order_detail_status = models.PositiveSmallIntegerField(
        "진행 상태", choices=STATUS_CHOICES, default=0)

    def get_order_detail_status_display(self):
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict.get(self.order_detail_status, "")

    def __str__(self):
        return f"OrderDetail #{self.id} - {self.get_order_detail_status_display()}"


class ShopImageFile(models.Model):
    '''
    작성자 : 장소은
    내용 : 상품 이미지 모델
    최초 작성일: 2023.06.06
    업데이트 일자:
    '''
    image_file = models.ImageField(null=True, blank=True)
    product = models.ForeignKey(
        ShopProduct, on_delete=models.CASCADE, related_name='images')


class RestockNotification(models.Model):
    '''
    작성자 : 장소은
    내용 : 재입고 알림 신청 모델, 사용자가 재입고 신청 시 DB에 저장 
    최초 작성일 : 2023.06.20
    '''
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(ShopProduct, on_delete=models.CASCADE)
    restock_created_at = models.DateTimeField(
        auto_now_add=True)
    notification_sent = models.BooleanField(default=False)
    restock_message = models.CharField(max_length=255, null=True, blank=True)

    # 중복방지
    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"User: {self.user.username}, Product: {self.product.product_name}"
