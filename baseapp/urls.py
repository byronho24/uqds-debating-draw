from django.urls import path

from . import views

app_name = 'baseapp'
urlpatterns = [
    path('', views.index, name='index'),
    path('debates/', views.debates, name='debates'),
    path('debates/<int:debate_id>/', views.detail, name='debate_detail'),
    path('signupform/', views.signupform, name='signupform'),
    path('attendanceform/', views.attendanceform, name='attendanceform'),
    path('table/', views.table, name='table'),
    path('record-results/', views.record_results, name='record_results'),
    path('record-results/<int:debate_id>/', views.record_results_detail, name="record_results_detail"),
    path('ajax/filter_speakers_in_team/', views.filter_speakers_in_team, name="filter_speakers_in_team"),
    path('ajax/filter_teams_in_debate', views.filter_teams_in_debate, name="filter_teams_in_debate"),
]
