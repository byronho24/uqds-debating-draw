from django.urls import path

from . import views

app_name = 'baseapp'
urlpatterns = [
    path('', views.index, name='index'),
    path('fixtures/', views.fixtures, name='fixtures'),
    path('fixtures/<int:match_id>/', views.detail, name='fixture_detail'),
    path('signupform/', views.signupform, name='signupform'),
    path('attendanceform/', views.attendanceform, name='attendanceform'),
]
