from django.urls import path
from . import views

urlpatterns = [
    # 유저 알림 조회
    path('notifications/', views.NotificationListAPIView.as_view(),
         name='notification_list'),

]
