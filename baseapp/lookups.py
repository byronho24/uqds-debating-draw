from ajax_select import register, LookupChannel
from .models import Speaker, Attendance, MatchDay
from django.utils import timezone

@register('speakers_team_signup')
class SpeakersLookupForTeamSignup(LookupChannel):

    model = Speaker

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q, team__isnull=True).order_by('name')[:50]

    def format_item_display(self, item):
        return f"<span class='speaker'>{item.name}</span>"

# @register('attendances_for_debate')
# class AttendancesLookupForDebate(LookupChannel):

#     model = Attendance

#     def get_query(self, q, request):
#         return self.model.objects.filter(timestamp__date=timezone.localdate(), team__name__icontains=q).order_by('team__name')


# @register('judges_for_debate')
# class JudgesLookupForDebate(LookupChannel):

#     model = Speaker

#     def get_query(self, q, request):
#         match_day = MatchDay.objects.get(date=timezone.localdate())
#         return match_day.judges.filter(name__icontains=q)
    