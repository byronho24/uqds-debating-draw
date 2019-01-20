from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from datetime import date, datetime
from . import allocator
from .forms import TeamAttendanceForm, TeamSignupForm
from .models import Attendance, Speaker, Team, Score, Match

def index(request):
    return render(request, 'baseapp/index.html')

def fixtures(request):

    # Check whether fixtures are already generated
    matches = Match.objects.filter(date=date.today())

    if not matches:
        # Generate fixtures
        # Retrieve all the attendance data for the day
        attendances = list(Attendance.objects.filter(timestamp__date=date.today()))
        competing_attendances, judges = allocator.assign_competing_teams(attendances)
        debates = allocator.matchmake(competing_attendances, judges)
        matches = []

        for debate in debates:
            # Save generated fixtures to database
            match = Match()
            match.date = date.today()
            match.judge = debate['judge']
            match.save()
            match.attendances.add(debate['attendance1'], debate['attendance2'])
            match.save()

            # add match to matches
            matches.append(match)

    return render(request, 'baseapp/fixtures.html', {'debates': matches})

def detail(request, match_id: int):
    # return HttpResponse(f"You are looking at match {match_id}.")
    # Get match based on match_id
    match = get_object_or_404(Match, pk=match_id)
    context = {'match': match}
    return render(request, 'baseapp/fixture_detail.html', context)

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
