from django import forms
from .models import Attendance, Speaker, Team, Debate, Score
from ajax_select.fields import AutoCompleteSelectMultipleField

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

        self.fields['speakers'] = AutoCompleteSelectMultipleField('speakers_team_signup', required=True)
        # Only speakers that are not in any team are available for selection
        self.fields['speakers'].help_text = \
            "<p id='speakersHelp' class='form-text text-muted'>" + \
            "Start typing to search for speakers by their name.<br>" + \
            "Only speakers that are already members of UQDS and are not already in a team are available for selection." + \
            "</p>"

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
