from django.urls import path

from . import views

app_name = 'attendanceform'
urlpatterns = [
    path('', views.markattendance, name='markattendance'),
    path('result', views.result, name="result")
]
