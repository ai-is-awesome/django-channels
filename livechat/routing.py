# Global routing configuration
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import chat.routing

application = ProtocolTypeRouter({
    # If a connection is a websocket connection,
    # the ProtocolTypeRouter will give this to our Middleware    
    'websocket': AuthMiddlewareStack(
        # AuthMiddlewareStack populates the connection's scope with a reference
        # to the currently authenticated user  
        URLRouter(
            # Finally, URLRouter examines the HTTP path
            # and route to a consumer, if any, using the chat application's urlpatterns
            chat.routing.websocket_urlpatterns
        )
    )
})