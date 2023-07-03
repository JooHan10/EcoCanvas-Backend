from django.urls import path
from chat import views

urlpatterns = [
    path("room/", views.RoomView.as_view(), name="room_view"),
    path("info/", views.ActiveRoomView.as_view(), name="info_view"),
    path("message/", views.GetRoomChatView.as_view(), name="message_view"),
]
