from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from django.conf.urls import url
from scriptpad import proxysshtowebsocket
application = ProtocolTypeRouter({
    # (http->django views is added by default)
'websocket': SessionMiddlewareStack(
    URLRouter(
        [

            url(r'^websocket/$', proxysshtowebsocket.AsyncConsumer),
        ]
    )
)
})