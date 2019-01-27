from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from datetime import date, datetime
from . import allocator
from .forms import TeamAttendanceForm, TeamSignupForm, DebateResultsForm, ScoreForm
from .models import Attendance, Speaker, Team, Score, Debate
from django.contrib import messages
from django.urls import reverse
from operator import itemgetter
from itertools import chain


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
    # if request.method == "GET":
    #     # GET requests used for filtering select items
    #     team_id = request.GET["team"];
    #     team = Team.objects.get(pk=team_id);
    #
    #
    if request.method == 'POST':
        print(request.POST)
        form = TeamAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your attendance has been marked.')

    form = TeamAttendanceForm()
    context = {
        'form': form,
    }
    return render(request, 'baseapp/attendanceform.html', context)

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

def record_results(request):
    # Get all the debates for that day
    # TODO: add selector for date
    debates = Debate.objects.filter(date=date.today())
    context = {'debates': []}
    for debate in debates:
        context["debates"].append(debate)

    return render(request, 'baseapp/record_results.html', context)


def record_results_detail(request, debate_id: int):
    debate = Debate.objects.get(pk=debate_id)

    if request.method == "POST":
        speaker_ids = [speaker.id for speaker in debate.attendance1.speakers.all()] + \
                            [speaker.id for speaker in debate.attendance2.speakers.all()]
        winning_team_form = DebateResultsForm(request.POST)
        speaker_score_forms = [ScoreForm(request.POST, prefix=str(id))
                                   for id in speaker_ids]

        if winning_team_form.is_valid() and all([sf.is_valid() for sf in speaker_score_forms]):
            # Update winner for debate
            debate.winning_team = winning_team_form.cleaned_data['winning_team']
            debate.save()

            # Record speaker's scores
            for sf in speaker_score_forms:
                sf.save()

            messages.success(request, "Results for this debate are successfully recorded.")

        else:
            messages.error(request, "Form details invalid. Please try again.")
    # Add speaker score forms
    attendances = []
    for attendance in [debate.attendance1, debate.attendance2]:
        team = {
            "team_name": attendance.team.name,
            "speakers": [],
        }
        for speaker in attendance.speakers.all():

            team["speakers"].append({
                'name': speaker.name,
                'score_form': ScoreForm(
                    prefix=str(speaker.id),
                    initial={
                        'speaker': speaker.id,
                        'debate': debate.id,
                })
            })
        attendances.append(team)

    context = {
        'debate_id': debate.id,
        'winning_team_form': DebateResultsForm(),
        'attendances': attendances,
    }

    return render(request, 'baseapp/record_results_detail.html', context)

def filter_speakers_in_team(request):
    team_id = request.GET.get('team_id', None);
    data = {
        "speakers": [],
    }
    if (team_id is not None) and team_id != '':
        team = Team.objects.get(pk=team_id)
        for speaker in team.speaker_set.all():
            data["speakers"].append(speaker.id)
    return JsonResponse(data)

def filter_teams_in_debate(request):
    debate_id = request.GET.get('debate_id', None);
    data = {}
    if (debate_id is not None) and debate_id != '':
        debate = Debate.objects.get(pk=debate_id)
        data['teams'] = [debate.attendance1.team.id, debate.attendance2.team.id]
    return JsonResponse(data)
