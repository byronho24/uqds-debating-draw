from django import forms
from .models import Attendance, Speaker, Team, Debate, Score
from searchableselect.widgets import SearchableSelect


class TeamAttendanceForm(forms.ModelForm):

    class Meta:
        model = Attendance
        fields = ('team', 'speakers', 'want_to_judge')
        labels = {
            'speakers': "Attending Speakers"
        }


class TeamSignupForm(forms.ModelForm):

    class Meta:
        model = Team
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['speakers'] = forms.ModelMultipleChoiceField(
            queryset=Speaker.objects.filter(team__isnull=True),
        )
        # Only speakers that are not in any team are available for selection

class DebateResultsForm(forms.ModelForm):

    class Meta:
        model = Debate
        fields = ('winning_team',)

class ScoreForm(forms.ModelForm):

    class Meta:
        model = Score
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['speaker'].widget = forms.HiddenInput()
        self.fields['debate'].widget = forms.HiddenInput()
