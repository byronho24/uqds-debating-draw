from django.urls import path

from . import views

urlpatterns = [
    path('', views.fixtures, name='fixtures'),
    path('<int:match_id>/', views.detail, name='detail')
]
