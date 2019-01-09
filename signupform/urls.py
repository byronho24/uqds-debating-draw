from django.urls import path

from . import views

urlpatterns = [
    path('', views.signupform, name='signupform'),
]
