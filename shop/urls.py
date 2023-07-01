from django.urls import path
from shop import views

urlpatterns = [
    path('products/list/', views.ProductListViewAPI.as_view(),
         name='product_sortby_view'),
    path('products/list/<int:category_id>/',
         views.ProductCategoryListViewAPI.as_view(), name='category_sortby_product_view'),
    path('products/<int:product_id>/',
         views.ProductDetailViewAPI.as_view(), name='product_detail_view'),
    path('products/admin/list/', views.AdminProductViewAPI.as_view(),
         name='admin_product_view'),
    path('categorys/list/', views.AdminCategoryViewAPI.as_view(),
         name='admin_category_view'),
    path('products/order/',
         views.OrderProductViewAPI.as_view(), name='order_view'),
    path('order/list/',
         views.AdminOrderViewAPI.as_view(), name='admin_order_view'),
    path('mypage/order/', views.MypageOrderViewAPI.as_view(), name='my_order_view'),
    path('products/restock/<int:product_id>/', views.RestockNotificationViewAPI.as_view(),
         name='restock_notification_view'),
    path('order/status/<int:order_id>/',
         views.HandleOrderStatusViewAPI.as_view(), name='order_status_view')
]
