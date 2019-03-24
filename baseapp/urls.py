from django.urls import path

from . import views

app_name = 'baseapp'
urlpatterns = [
    path('', views.index, name='index'),
    path('draw/', views.debates, name='debates'),
    path('draw/<int:debate_id>/', views.detail, name='debate_detail'),
    path('signupform/', views.signupform, name='signupform'),
    path('attendanceform/', views.attendanceform, name='attendanceform'),
    # path('table/', views.table, name='table'),
    path('upload_data/', views.upload_speaker_data, name="upload_speaker_data")
    path('simulate-rounds/', views.simulate_rounds, name='simulate_rounds'),

    path('generate-debates', views.generate_debates, name="generate_debates"),
    path('ajax/filter_speakers_in_team/', views.filter_speakers_in_team, name="filter_speakers_in_team"),
    path('ajax/filter_debate_details', views.filter_debate_details, name="filter_debate_details"),
]