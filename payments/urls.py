from django.urls import path
from payments import views

urlpatterns = [    
    path('register/', views.RegisterCustomerView.as_view(), name='register_payment' ),
    path('schedule/<int:pk>', views.CreatePaymentScheduleView.as_view(), name='schedule_payment'),
    path('schedule/receipt/', views.ScheduleReceiptAPIView.as_view(), name='schedule_receipt_payment'),
    path('schedule/detail/<int:pk>', views.DetailScheduleReceiptAPIView.as_view(), name='schedule_receipt_payment'),
    path('receipt/<int:user_id>', views.ReceiptAPIView.as_view(), name='receipt_payment'),
    path('receipt/detail/<int:pk>', views.DetailReciptAPIView.as_view(), name='receipt_detail'),
    path('refund/<int:pk>', views.RefundpaymentsAPIView.as_view(), name='refund_payment'),
    path('receipt/refund/<int:pk>', views.RefundReceiptAPIView.as_view(), name='refund_receipt')
]