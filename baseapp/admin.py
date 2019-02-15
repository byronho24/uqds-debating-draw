from django.contrib import admin

from .models import Team, Speaker, Attendance, Debate, Score
from .views import record_results
from django.urls import path, include
from datetime import datetime
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib import messages



class ScoreInstanceInlineForDebate(admin.TabularInline):
    model = Score
    extra = 0
    can_delete = False

    def get_min_num(self, request, obj=None, **kwargs):
        max_num = 6
        if obj:
            max_num = 0
            for attendance in obj.get_attendances():
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
    list_display = ("name", "count_qualified_judges")
    inlines = [SpeakerInstanceInline]

class MyDebateAdmin(admin.ModelAdmin):
    list_display_links = ('date',)
    list_display = (
        'date',
        'attendance1', 'attendance2', 'judge'
    )
    list_filter = ('date',)
    # list_editable = (
    #     'attendance1', 'attendance2', 'judge',
    # )
    inlines = [ScoreInstanceInlineForDebate]
    autocomplete_fields = ['attendance1', 'attendance2']

    def has_add_permission(self, request, obj=None):
        return False

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "attendance1" or db_field.name == "attendance2":
    #         kwargs["queryset"] = Attendance.objects.filter(timestamp__date=datetime.today())
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def get_readonly_fields(self, request, obj):
        if obj.date != datetime.today():
            return ("attendance1", "attendance2", 'judge')

    def save_model(self, request, obj, form, change):
        
        super().save_model(request, obj, form, change)

        # Post-save --> update team wins
        for attendance in obj.get_attendances():
            team = attendance.team
            wins = Debate.objects.filter(winning_team=team).count()
            team.wins = wins
            team.save()

        # Update team judged_before
        Team.objects.filter(pk=obj.judge.team.id).update(judged_before=True)

    def save_formset(self, request, form, formset, change):
        # get all the objects in the formset
        instances = formset.save(commit=False)

        for instance in instances:
            # Perform custom validation
            try:
                instance.clean()
            except ValidationError as e:
                # Display error to user
                messages.error(request, str(e))
            else:
                instance.save()

class MySpeakerAdmin(admin.ModelAdmin):
    # inlines = [ScoreInstanceInlineForSpeaker]
    list_display = ("name", "team", "judge_qualification_score")
    list_filter = ("team",)

class MyScoreAdmin(admin.ModelAdmin):
    list_display = ('speaker', 'debate')


class MyAttendanceAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "team", "count_qualified_judges")
    list_filter = ("timestamp", "team")

    # Allow search for attendances by team name
    ordering = ['-timestamp']
    search_fields = ['team__name']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        queryset = queryset.filter(timestamp__date=datetime.today())
        return queryset, use_distinct


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