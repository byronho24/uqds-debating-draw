from django.urls import path

from . import views

urlpatterns = [
    path('', views.fixtures, name='fixtures'),
]
