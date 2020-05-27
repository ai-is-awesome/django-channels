import os
import json
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from .chatbot import room_to_chatbot_user, ChatBotUser

# Asynchronous websocket consumer
# Our suitable websocket routes will end up here
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # TODO: Accept only if the user is authorized
        # Make accept() as the last call
        await self.accept()
        print(f"Connected")
        try:
            self.chatbot_user = room_to_chatbot_user[self.room_name]
        except KeyError:
            self.chatbot_user = room_to_chatbot_user['default']
        print(f"Redirecting you to {self.chatbot_user}....")
        self.chatbot = ChatBotUser(self.chatbot_user, os.path.join(os.getcwd(), "chat\\templates\\chat\\" + self.chatbot_user + ".json"))
        # print(self.chatbot.content)
        self.curr_state = 1
        # self.send(text_data=f"Welcome user!")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print("Disconnected!")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # reply = sync_to_async(self.chatbot.process_message(message))
        # Send the message to our group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )
        
        if self.curr_state != -1:
            reply, curr_state = self.chatbot.process_message(message, self.curr_state)
            if isinstance(reply, tuple):
                curr_state = reply[1]
                reply = reply[0]
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': reply
                }
            )
            self.curr_state = curr_state
    
    # Receive message from the same room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))