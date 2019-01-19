from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import TeamSignupForm
from fixtures.models import Team
from django.contrib import messages

context = {
    'speaker_ids': [1, 2, 3, 4, 5]
}

def _contains_duplicates(l):
    return len(set(l)) != len(l)

def index(request):
    return render(request, 'signupform/index.html', context)

def signup(request):

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
    return render(request, 'signupform/form.html', {'form': form})
