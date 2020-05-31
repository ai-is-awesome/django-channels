# Routing configuration for the application
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer),
    #re_path(r'ws/livechat/(?P<room_name>\w+)/$', consumers.AdminChatConsumer),
    re_path(r'ws/adminchat/(?P<room_name>\w+)/$', consumers.AdminChatConsumer),
]


