from django.contrib import admin

from .models import Team, Speaker, Attendance, Match
# Register your models here.
admin.site.register(Team)
admin.site.register(Speaker)
admin.site.register(Attendance)
admin.site.register(Match)
