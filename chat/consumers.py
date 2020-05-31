import os
import json
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from .chatbot import room_to_chatbot_user, ChatBotUser

num_users = 0

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
        user = self.scope['user']
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # reply = sync_to_async(self.chatbot.process_message(message))
        # Send the message to our group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message_from_client',
                'message': message,
            }
        )
        
        if self.curr_state != -1:
            reply, curr_state, msg_type = self.chatbot.process_message(message, self.curr_state, user)
            
            print(f'Returned with reply {reply} with type = {msg_type}')
            
            if isinstance(reply, tuple):
                msg_type = reply[2]
                curr_state = reply[1]
                reply = reply[0]
            
            if msg_type == None:
                msg_type = 'None'
            
            # Sending high-level events over the channel layer
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_to_client',
                    'room_name': self.room_name,
                    'message': reply,
                    'message_type': msg_type,
                }
            )
            
            self.curr_state = curr_state
    
    
    async def chat_message_from_client(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
        }))


    async def chat_message_to_client(self, event):
        await self.send(text_data=json.dumps({
        'room_name': event['room_name'],
            'message': event['message'],
            'message_type': event['message_type'],
        }))
    
    # Chat messages from admin
    async def chat_message(self, event):
        print('Received msg from admin')
        await self.send(text_data=json.dumps({
            'message': event['message'],
            }))










class AdminChatConsumer(WebsocketConsumer):
    def connect(self):
        global num_users
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        self.num_members = 0

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        num_users += 1
        self.user_id = num_users

        user = self.scope['user']
        print(f'user is {user}{num_users}')


        
        if user.is_authenticated and user.is_superuser:
            print('User is admin')
            self.accept()
            self.num_members += 1
            print(f"Now room has {self.num_members} members")
        else:
            print('User isnt admin')
            if self.num_members == 0:
                print('First member. Waiting for the admin...')
                self.accept()
                self.num_members += 1
                print(f"Now room has {self.num_members} members")
            else:
                print("Too many members. Cannot join this room. Sorry")


    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        self.num_members -= 1
        print(f"Now room has {self.num_members} members")

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        # print(f"{self.user_id} sent message")
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))












