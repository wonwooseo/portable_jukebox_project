from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/skipadd/', consumers.SkipAddConsumer),
    path('ws/music/', consumers.MusicConsumer),
]
