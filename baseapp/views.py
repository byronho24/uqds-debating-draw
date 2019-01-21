from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from datetime import date, datetime
from . import allocator
from .forms import TeamAttendanceForm, TeamSignupForm
from .models import Attendance, Speaker, Team, Score, Debate
from django.contrib import messages
from django.urls import reverse
from operator import itemgetter


def index(request):
    return render(request, 'baseapp/index.html')

def debates(request):

    # Check whether debates are already generated
    debates = Debate.objects.filter(date=date.today())

    if not debates:
        # Generate debates
        # Retrieve all the attendance data for the day
        attendances = list(Attendance.objects.filter(timestamp__date=date.today()))
        debates = allocator.generate_debates(attendances)

    return render(request, 'baseapp/debates.html', {'debates': debates})

def detail(request, debate_id: int):
    # return HttpResponse(f"You are looking at debate {debate_id}.")
    # Get debate based on debate_id
    debate = get_object_or_404(Debate, pk=debate_id)
    context = {'debate': debate}
    return render(request, 'baseapp/debate_detail.html', context)

def attendanceform(request):
    if request.method == 'POST':
        form = TeamAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your attendance has been marked.')

    form = TeamAttendanceForm()
    return render(request, 'baseapp/attendanceform.html', {'form': form})

def signupform(request):

    if request.method == 'POST':
        form = TeamSignupForm(request.POST)
        if form.is_valid():
            team_name = form.cleaned_data['name']
            speakers = form.cleaned_data['speakers']

            # Create team
            team = Team(name = team_name)
            team.save()

            # Assign team to speakers
            for speaker in speakers:
                if speaker is not None:
                    speaker.team = team
                    speaker.save()

            messages.success(request, 'Team signup successful.')


    form = TeamSignupForm()
    return render(request, 'baseapp/signupform.html', {'form': form})

def table(request):
    # Gets all the teams
    teams = list(Team.objects.all())
    # TODO: Sort teams based on wins
    sorting_list = []
    for team in teams:
        sorting_list.append((team.wins, team.get_speakers_avg_score(), team))
    sorting_list.sort(key=itemgetter(0,1), reverse=True)
    sorted_teams = []
    for item in sorting_list:
        team = item[2]
        sorted_teams.append({
            'name': team.name,
            'wins': team.wins,
            'speaker_avg_score': team.get_speakers_avg_score(),
        })
    context = {
        'teams': sorted_teams,
    }
    return render(request, 'baseapp/table.html', context)
