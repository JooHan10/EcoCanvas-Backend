from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/alarm/$', consumers.ChatNotificationConsumer.as_asgi()),
    re_path(r'ws/notification/$', consumers.NotificationConsumer.as_asgi()),
    # re_path(r'ws/login/$', consumers.LoginConsumer.as_asgi()),

]
