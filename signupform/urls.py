from django.urls import path

from . import views

app_name = 'signupform'
urlpatterns = [
    path('', views.signup, name='signup'),
]
