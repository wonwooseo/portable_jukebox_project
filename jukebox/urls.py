from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('check_password', views.check_password, name='check_password'),
    path('nowplaying', views.now_playing, name='now_playing')
]