from channels.routing import ProtocolTypeRouter, URLRouter

import jukebox.routing

application = ProtocolTypeRouter({
    'websocket': URLRouter(
            jukebox.routing.websocket_urlpatterns
    ),
})
