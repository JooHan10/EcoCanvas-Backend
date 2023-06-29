import json
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Room, Message
from users.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    def last_30_messages(self, room_id):
        return Message.objects.filter(room_id=room_id).order_by('created_at')[:30]

    async def fetch_messages(self, data):
        """
        작성자 : 박지홍
        내용 : 웹 소켓을 통해 메시지를 조회하고 메시지를 클라이언트로 전송하는 함수.
        최초 작성일 : 2023.06.06
        업데이트 일자 : 2023.06.15
        #06.15 : 동기 기반 클레스에서 비동기 기반으로 변경
        """
        room_id = int(self.room_name)
        user_id = data["user_id"]

        user_contact = await sync_to_async(User.objects.get)(id=user_id)
        room_contact = await sync_to_async(Room.objects.get)(id=room_id)
        
        messages = await sync_to_async(self.last_30_messages)(room_id=room_id)
        json_message = await sync_to_async(self.messages_to_json)(messages)
        content = {"command": "messages",
                   "messages": json_message}

        await self.send_message(message=content)

    async def new_message(self, data):
        """
        작성자 : 박지홍
        내용 : 웹 소켓을 통해 새로운 메시지를 처리하고 메시지를 클라이언트로 전송하는 함수.
        최초 작성일 : 2023.06.06
        업데이트 일자 : 2023.06.15
        #06.15 : 동기 기반 클레스에서 비동기 기반으로 변경
        """
        user_id = data["user_id"]
        room_id = int(self.room_name)

        user_contact = await sync_to_async(User.objects.get)(id=user_id)
        room_contact = await sync_to_async(Room.objects.get)(id=room_id)
        message_creat = await sync_to_async(Message.objects.create)(
            user_id=user_contact, room_id=room_contact, message=data["message"]
        )
        
        message = await sync_to_async(self.message_to_json)(message_creat)
        content = {
            "command": "new_message",
            "message": message,
        }
        await self.send_chat_message(content)

        is_active = not self.user.is_staff
        await self.room_set_activate(room_contact, is_active)


    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))
        return result

    def message_to_json(self, message):
        return {
            "author": message.user_id.email,
            "content": message.message,
            "timestamp": str(message.created_at),
        }

    async def room_set_activate(self, room, active):
        room.is_active = active
        await sync_to_async(room.save)()


    commands = {"fetch_messages": fetch_messages, "new_message": new_message}

    async def connect(self):
        """
        작성자 : 박지홍
        내용 : 웹 소켓이 연결을 처리하는 함수.
        최초 작성일 : 2023.06.06
        업데이트 일자 : 2023.06.15
        #06.15 : 동기 기반 클레스에서 비동기 기반으로 변경
        """
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.user = self.scope['user']
        self.room_group_name = "chat_%s" % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        if self.user.is_staff:
            room = await sync_to_async(Room.objects.get)(id=self.room_name)
            room.counselor = self.user
            await sync_to_async(room.save)()

        await self.accept()

    async def disconnect(self, close_code):
        """
        작성자 : 박지홍
        내용 : 웹 소켓이 연결이 종료될 때 호출되는 함수.
        최초 작성일 : 2023.06.06
        업데이트 일자 : 2023.06.15
        #06.15 : 동기 기반 클레스에서 비동기 기반으로 변경
        """

        if self.user.is_staff:
            room = await sync_to_async(Room.objects.get)(id=self.room_name)
            room.counselor = None
            await sync_to_async(room.save)()

        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        """
        작성자 : 박지홍
        내용 : 웹 소켓으로 부터 메시지를 수신할 때 호출되는 함수.
        최초 작성일 : 2023.06.06
        업데이트 일자 : 2023.06.15
        #06.15 : 동기 기반 클레스에서 비동기 기반으로 변경
        """
        data = json.loads(text_data)
        await self.commands[data["command"]](self, data)

    async def send_chat_message(self, message):
        """
        작성자 : 박지홍
        내용 : 채팅 메시지를 웹 소켓으로 전송하는 함수. 
            - 하단의 send_message, chat_message 도 동일 기능 수행.
        최초 작성일 : 2023.06.06
        업데이트 일자 : 2023.06.15
        #06.15 : 동기 기반 클레스에서 비동기 기반으로 변경
        """
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message}
        )

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))
