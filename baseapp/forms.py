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
        help_texts = {
            'want_to_judge':
                    "Note that this does not guarantee that you would judge/not judge; but "+\
                        "if checked, this would inform the allocation system to place your team at a higher "+\
                            "priority for judging.",
            'team':
                    "Only 1 person from each team should complete this weekly attendance form.<br>" + \
                    "You must select ALL speakers who are here this week.<br>"
                    "You can change your attendance as many times as you like, only the " +\
                        "most recent submission will be used.",
            'speakers':
                    "Hold down Ctrl/Cmd to select more than one speaker"
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
