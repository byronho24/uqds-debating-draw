from django.contrib import admin

from .models import Team, Speaker, Attendance, Debate, Score
from .views import record_results
from django.urls import path, include


class ScoreInstanceInlineForDebate(admin.TabularInline):
    model = Score
    extra = 0
    can_delete = False

    def get_min_num(self, request, obj=None, **kwargs):
        max_num = 6
        if obj:
            max_num = 0
            for attendance in obj.attendance_set.all():
                max_num += len(attendance.speakers.all())

        return max_num

    def get_max_num(self, request, obj=None, **kwargs):
        return self.get_min_num(request, obj, **kwargs)

class ScoreInstanceInlineForSpeaker(admin.TabularInline):
    model = Score
    extra = 0
    can_delete = False
    fields = ("debate", "score")

    def get_min_num(self, request, obj=None, **kwargs):
        return obj.score_set.count()

    def get_max_num(self, request, obj=None, **kwargs):
        return self.get_min_num(request, obj, **kwargs)

class SpeakerInstanceInline(admin.TabularInline):
    model = Speaker
    extra = 0
    can_delete = False

class MyTeamAdmin(admin.ModelAdmin):
    inlines = [SpeakerInstanceInline]

class MyDebateAdmin(admin.ModelAdmin):

    list_display = ('date',
        #'team1', 'team2'
    )
    list_filter = ('date',)
    readonly_fields = ("date", "judge")
    inlines = [ScoreInstanceInlineForDebate]

    def team1(self, obj):
        return obj.attendance_set.all()[0].team.name

    def team2(self, obj):
        return obj.attendance_set.all()[1].team.name

class MySpeakerAdmin(admin.ModelAdmin):
    inlines = [ScoreInstanceInlineForSpeaker]
    list_display = ("name", "team",)

class MyScoreAdmin(admin.ModelAdmin):
    list_display = ('speaker', 'debate')


class MyAttendanceAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "team")
    list_filter = ("timestamp", "team")

class MyAdminSite(admin.AdminSite):
    site_header = "UQ Debating Society Internals Administration"
    site_title = "UQDS Admin"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('record_results', self.admin_view(record_results)),
        ]
        return urls + my_urls

admin_site = MyAdminSite(name="myadmin")
admin_site.register(Team, MyTeamAdmin)
admin_site.register(Speaker, MySpeakerAdmin)
admin_site.register(Attendance, MyAttendanceAdmin)
admin_site.register(Score, MyScoreAdmin)
admin_site.register(Debate, MyDebateAdmin)
