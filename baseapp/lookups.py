from ajax_select import register, LookupChannel
from .models import Speaker

@register('speakers_team_signup')
class SpeakersLookupForTeamSignup(LookupChannel):

    model = Speaker

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q, team__isnull=True).order_by('name')[:50]

    def format_item_display(self, item):
        return f"<span class='speaker'>{item.name}</span>"