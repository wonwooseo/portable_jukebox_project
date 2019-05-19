from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('check_password', views.check_password, name='check_password'),
    path('nowplaying', views.now_playing, name='now_playing'),
    path('qrcode', views.qrcode, name='qrcode'),
    path('add', views.add, name='add'),
    path('add_youtube', views.add_youtube, name='add_youtube')
]
