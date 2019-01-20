from django.urls import path

from . import views

app_name = 'baseapp'
urlpatterns = [
    path('', views.index, name='index'),
    path('debates/', views.debates, name='debates'),
    path('debates/<int:debate_id>/', views.detail, name='debate_detail'),
    path('signupform/', views.signupform, name='signupform'),
    path('attendanceform/', views.attendanceform, name='attendanceform'),
]
