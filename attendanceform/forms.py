from django import forms
from fixtures.models import Attendance, Speaker
from searchableselect.widgets import SearchableSelect


class TeamAttendanceForm(forms.ModelForm):

    class Meta:
        model = Attendance
        exclude = ('timestamp',)
        labels = {
            'speakers': "Attending Speakers"
        }
