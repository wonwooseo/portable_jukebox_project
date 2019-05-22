from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('check_password', views.check_password, name='check_password'),
    path('nowplaying', views.now_playing, name='now_playing'),
    path('qrcode', views.qrcode, name='qrcode'),
    path('add', views.add, name='add'),
    path('add_youtube', views.add_youtube, name='add_youtube'),
    path('search_youtube', views.search_youtube, name='search_youtube'),
    path('add_youtube_item', views.add_youtube_item, name='add_youtube_item'),
    path('add_file', views.add_file, name='add_file'),
    path('add_file_item', views.add_file_item, name='add_file_item')
]
