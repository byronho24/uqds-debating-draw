from django.urls import path

from . import views

app_name = 'signupform'
urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup')
]
