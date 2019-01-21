from django import forms
from .models import Attendance, Speaker, Team
from searchableselect.widgets import SearchableSelect


class TeamAttendanceForm(forms.ModelForm):

    class Meta:
        model = Attendance
        exclude = ('timestamp',)
        labels = {
            'speakers': "Attending Speakers"
        }


class TeamSignupForm(forms.ModelForm):

    class Meta:
        model = Team
        exclude = ('wins', 'judged_before')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['speakers'] = forms.ModelMultipleChoiceField(
            queryset=Speaker.objects.filter(team__isnull=True),
        )
        # Only speakers that are not in any team are available for selection
