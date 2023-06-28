from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class ChatNotificationConsumer(WebsocketConsumer):
    '''
    작성자 : 장소은
    내용 : 웹소켓 연결, notification_admin_group의 모든 컨슈머에게 메세지 보내기 
    최초 작성일: 2023.06.25
    '''

    def connect(self):
        # notification_admin_group 그룹에 컨슈머 추가(알림 메세지 수신),
        async_to_sync(self.channel_layer.group_add)(
            "notification_admin_group", self.channel_name)
        self.accept()  # 웹 소켓 연결 수락

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            "notification_admin_group", self.channel_name)

    def receive(self, text_data):
        pass

    def send_admin_notification(self, event):
        message = event['message']
        self.send(text_data=message)


class NotificationConsumer(WebsocketConsumer):
    '''
    작성자 : 장소은
    내용 : 웹소켓 연결, notification_group의 모든 컨슈머에게 메세지 보내기
    최초 작성일: 2023.06.21
    '''

    def connect(self):
        # notification_group 그룹에 컨슈머 추가(알림 메세지 수신),
        async_to_sync(self.channel_layer.group_add)(
            "notification_group", self.channel_name)
        self.accept()  # 웹 소켓 연결 수락

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            "notification_group", self.channel_name)

    def receive(self, text_data):
        pass

    def notification_message(self, event):
        message = event['message']
        self.send(text_data=message)


# class LoginConsumer(WebsocketConsumer):
#     '''
#     작성자 : 장소은
#     내용 : 웹소켓 연결, notification_login_group 모든 컨슈머에게 메세지 보내기
#     최초 작성일: 2023.06.22
#     '''

#     def connect(self):
#         # notification_login_group 그룹에 컨슈머 추가(알림 메세지 수신),
#         async_to_sync(self.channel_layer.group_add)(
#             "notification_login_group", self.channel_name)
#         self.accept()  # 웹 소켓 연결 수락

#     def disconnect(self, close_code):
#         async_to_sync(self.channel_layer.group_discard)(
#             "notification_login_group", self.channel_name)

#     def receive(self, text_data):
#         pass

#     def notification_message(self, event):
#         message = event['message']
#         self.send(text_data=message)
