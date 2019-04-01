from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from datetime import date, datetime, timedelta
from django.utils import timezone
from . import allocator
from .forms import TeamAttendanceForm, TeamSignupForm, DebateResultsForm, ScoreForm
from .models import Attendance, Speaker, Team, Score, Debate, MatchDay
from .exceptions import NotEnoughJudgesException, CannotFindWorkingConfigurationException, NotEnoughAttendancesException, NotEnoughRoomsException
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.urls import reverse
from operator import itemgetter
from itertools import chain

def stringify(l):
    """ Concatenates list of strings into a comma-separated string. """
    result = ""
    for string in l:
        result += string + ", "
    # Remove trailing comma and space
    result = result[:-2]
    return result

def index(request):
    return render(request, 'baseapp/index.html')

def debates(request):
    # Check if debates are finalised
    try:
        match_day = MatchDay.objects.get(date=timezone.localdate())
        debates = list(match_day.debate_set.all())
    except ObjectDoesNotExist:
        debates = []

    context = {
        'debates': []
    }

    for debate in debates:

        context['debates'].append({
            'debate_id': debate.id,
            'room': debate.room.name if debate.room else '',
            'team1': {
                'name': debate.affirmative.team.name,
                'speakers': debate.affirmative.speakers.all()
            },
            'team2': {
                'name': debate.negative.team.name,
                'speakers': debate.negative.speakers.all()
            },
            'judges': stringify([judge.name for judge in debate.judges.all()])
        })

    return render(request, 'baseapp/debates.html', context)

def detail(request, debate_id: int):
    # return HttpResponse(f"You are looking at debate {debate_id}.")
    # Get debate based on debate_id
    debate = get_object_or_404(Debate, pk=debate_id)

    context = {
        'debate_id': debate.id,
        'team1': {
            'name': debate.affirmative.team.name,
            'speakers': debate.affirmative.team.speaker_set.all()
        },
        'team2': {
            'name': debate.negative.team.name,
            'speakers': debate.negative.team.speaker_set.all()
        },
    }
    return render(request, 'baseapp/debate_detail.html', context)

def attendanceform(request):
    if request.method == 'POST':
        form = TeamAttendanceForm(request.POST)
        if form.is_valid():
            if len(form.cleaned_data["speakers"]) > 3:
                messages.error(request, 'Please select up to 3 speakers.')
                return HttpResponseRedirect(reverse("baseapp:attendanceform"))
            
            # Update attendance entry if attendance already exists for team, else create
            attendance, created = Attendance.objects.update_or_create(
                team=form.cleaned_data["team"],
                date=timezone.localdate(),
                defaults={
                    'want_to_judge': form.cleaned_data["want_to_judge"]
                }
            )
            attendance.speakers.set(form.cleaned_data["speakers"])
            attendance.save()

            if created:
                messages.success(request, "Your attendance has been marked.")
            else:
                messages.success(request, 'Your attendance has been updated.')
            return HttpResponseRedirect(reverse("baseapp:attendanceform"))

    # Only show form if MatchDay has not been finalised
    form = TeamAttendanceForm()
    context = {
        'form': form,
        'show_form': True
        # 'show_form': MatchDay.objects.filter(date=timezone.localdate()).exists()
    }
    return render(request, 'baseapp/attendanceform.html', context)

def signupform(request):

    if request.method == 'POST':
        form = TeamSignupForm(request.POST)
        if form.is_valid():
            team_name = form.cleaned_data['name']
            speakers = form.cleaned_data['speakers']
                
            if len(speakers) > Team.MAX_SPEAKERS:
                messages.error(request, "Please select up to 5 speakers.")
                return HttpResponseRedirect(reverse("baseapp:signupform"))
            
            # Create team
            team = Team(name = team_name)
            team.save()

            # Assign team to speakers
            for speaker_id in speakers:
                try:
                    id = int(speaker_id)
                except TypeError:
                    messages.error(request, "An error occurred - please try again later.")
                    return HttpResponseRedirect(reverse("baseapp:signupform"))
                
                speaker = Speaker.objects.get(pk=id)
                speaker.team = team
                speaker.save()

            messages.success(request, 'Team signup successful.')
            return HttpResponseRedirect(reverse("baseapp:signupform"))
        
        else:
            messages.error(request, "Form invalid - either no speakers were selected or team name has already been taken.")

    form = TeamSignupForm()
    context = {
        'form': form,
        'show_form': True
    }
    return render(request, 'baseapp/signupform.html', context)

def table(request):
    # Gets all the teams
    teams = list(Team.objects.all())

    sorting_list = []
    for team in teams:
        sorting_list.append((team.get_wins(), team.get_speakers_avg_score(), team))
    sorting_list.sort(key=itemgetter(0,1), reverse=True)
    sorted_teams = []
    for item in sorting_list:
        team = item[2]
        sorted_teams.append({
            'name': team.name,
            'wins': team.get_wins(),
            'speaker_avg_score': "%.2f" % team.get_speakers_avg_score(),
        })
    context = {
        'teams': sorted_teams,
    }
    return render(request, 'baseapp/table.html', context)

def simulate_rounds(request):
    from .test_allocator import simulate_rounds
    match_days = []
    if request.method == 'POST':
        rounds = int(request.POST['rounds'])
        try:
            match_days = simulate_rounds(rounds)
        except Exception as err:
            messages.error(request, str(err))
    # match_days = simulate_rounds(1)
    return render(request, 'baseapp/simulate_rounds.html', {'match_days': match_days})


def upload_speaker_data(request):
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage, File
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(myfile.name, myfile)

        from .importer import import_speaker_data
        file_path = settings.MEDIA_ROOT + '/' + myfile.name
        if import_speaker_data(file_path):
            messages.success(request, "Speaker data imported successfully.")
        else:
            messages.error(request, "Errors occurred while importing speaker data.")
    return render(request, "baseapp/file_upload.html")


# def record_results(request):
#     # Get all the debates for that week
#     today = timezone.localdate()
#     start_date = today - timedelta(days=6)
#     debates = Debate.objects.filter(date__range=(start_date, today))
#     context = {'debates': []}
#     for debate in debates:
#         context["debates"].append(debate)

#     return render(request, 'baseapp/record_results.html', context)


# def record_results_detail(request, debate_id: int):
#     debate = Debate.objects.get(pk=debate_id)

#     if request.method == "POST":
#         speaker_ids = [speaker.id for speaker in debate.affirmative.speakers.all()] + \
#                             [speaker.id for speaker in debate.negative.speakers.all()]
#         winning_team_form = DebateResultsForm(request.POST)
#         speaker_score_forms = [ScoreForm(request.POST, prefix=str(id))
#                                    for id in speaker_ids]

#         if winning_team_form.is_valid() and all([sf.is_valid() for sf in speaker_score_forms]):
#             # Update winner for debate
#             debate.winning_team = winning_team_form.cleaned_data['winning_team']
#             debate.save()

#             # Update team judged_before
#             Team.objects.filter(pk=debate.judge.team.id).update(judged_before=True)

#             # Record speaker's scores
#             for sf in speaker_score_forms:
#                 # Update if score object already exists, else create
#                 obj, created = Score.objects.update_or_create(
#                     debate = sf.cleaned_data["debate"],
#                     speaker = sf.cleaned_data["speaker"],
#                     defaults={
#                         'score': sf.cleaned_data["score"]
#                     }
#                 )

#             messages.success(request, "Results for this debate are successfully recorded.")
#             return HttpResponseRedirect(reverse("baseapp:record_results_detail", args=[debate_id]))

#         else:
#             messages.error(request, "Form details invalid. Please try again.")

#     # Add speaker score forms
#     attendances = []
#     for attendance in debate.get_attendances():
#         team = {
#             "team_name": attendance.team.name,
#             "speakers": [],
#         }
#         for speaker in attendance.speakers.all():

#             team["speakers"].append({
#                 'name': speaker.name,
#                 'score_form': ScoreForm(
#                     prefix=str(speaker.id),
#                     initial={
#                         'speaker': speaker.id,
#                         'debate': debate.id,
#                         'score': speaker.score_set.get(debate=debate).score \
#                                     if Score.objects.filter(speaker=speaker, debate=debate).exists() \
#                                     else None
#                 })
#             })
#         attendances.append(team)

#     context = {
#         'debate_id': debate.id,
#         'winning_team_form': DebateResultsForm(initial={
#             'winning_team': debate.winning_team if debate.winning_team is not None else None
#         }),
#         'attendances': attendances,
#     }

#     return render(request, 'baseapp/record_results_detail.html', context)

def filter_speakers_in_team(request):
    team_id = request.GET.get('team_id', None)
    data = {
        "speakers": [],
    }
    if (team_id is not None) and team_id != '':
        team = Team.objects.get(pk=team_id)
        for speaker in team.speaker_set.all():
            data["speakers"].append(speaker.id)
    return JsonResponse(data)

def filter_debate_details(request):
    debate_id = request.GET.get('debate_id', None)
    data = {
        'teams': [],
        'speakers': []
    }
    if (debate_id is not None) and debate_id != '':
        debate = Debate.objects.get(pk=debate_id)
        data['teams'] = [attendance.team.id for attendance in debate.get_attendances()]
        for attendance in debate.get_attendances():
            data['speakers'] += [
                {
                    'id': speaker.id,
                    'name': speaker.name,
                    'team': speaker.team.name,
                }
                for speaker in attendance.speakers.all()
            ]
    return JsonResponse(data)

def generate_debates(request):
    match_day = MatchDay.objects.filter(date=timezone.localdate())
    if match_day:
        messages.warning(
            request, 
            "Debates already generated. Please select the matchday for today below to edit the debates."
        )
    else:
        try:
            match_day = allocator.generate_debates(date=timezone.localdate())
        except NotEnoughAttendancesException as nea:
            messages.error(request, str(nea))
        except NotEnoughJudgesException as nej:
            messages.error(request, str(nej))
        except NotEnoughRoomsException as ner:
            messages.error(request, str(ner))
        except CannotFindWorkingConfigurationException as e:
            messages.error(request, str(e))
        else:
            messages.success(request, "Please review the debates generated, and click 'Save' once you are happy with the allocated debates.")
            return HttpResponseRedirect(f"/admin/baseapp/matchday/{match_day.id}/change/")

    # TODO: fix hard-coded url
    return HttpResponseRedirect("/admin/baseapp/matchday/")