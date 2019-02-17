from django.contrib import admin

from .models import Team, Speaker, Attendance, Debate, Score, MatchDay
from django.urls import path, include
from django.utils import timezone
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib import messages
from ajax_select import make_ajax_form


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

class DebateInstanceInline(admin.TabularInline):
    model = Debate
    extra = 0
    can_delete = False
    exclude = ["winning_team"]
    # autocomplete_fields = ["attendance1", "attendance2"]
    show_change_link = True
    # form = make_ajax_form(Debate, {
    #     'attendance1': 'attendances_for_debate',
    #     'attendance2': 'attendances_for_debate',
    #     'judges': 'judges_for_debate'
    # })

    def get_max_num(self, request, obj=None, **kwargs):
        if obj.date != timezone.localdate():
            return Debate.objects.filter(match_day=obj).count()
        else:
            return super().get_max_num(self, request, obj=None, **kwargs)

    def get_readonly_fields(self, request, obj):
        if obj.date != timezone.localdate():
            return ("attendance1", "attendance2", 'judges')
        else:
            return tuple()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "attendance1" or db_field.name == "attendance2":
            try:
                match_day = MatchDay.objects.get(date=timezone.localdate())
                kwargs["queryset"] = match_day.attendances_competing.all()
            except MatchDay.DoesNotExist:
                # Then no need to change queryset
                pass
        # TODO: order these attendances
        # TODO: dynamic filtering based on selected teams/judges
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "judges":
            try:
                match_day = MatchDay.objects.get(date=timezone.localdate())
                kwargs["queryset"] = match_day.attendances_competing.all()
            except MatchDay.DoesNotExist:
                # Then no need to change queryset
                pass
        return super().formfield_for_manytomany(db_field, request, **kwargs)

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

class MyTeamAdmin(admin.ModelAdmin):
    list_display = ("name", "wins", "count_qualified_judges")
    inlines = [SpeakerInstanceInline]

    def wins(self, obj):
        return obj.get_wins()

    def has_add_permission(self, request, obj=None):
        return False


class MyDebateAdmin(admin.ModelAdmin):
    list_display = (
        'match_day', 'attendance1', 'attendance2'
    )
    list_filter = ('match_day',)
    # list_editable = (
    #     'attendance1', 'attendance2', 'judges',
    # )
    inlines = [ScoreInstanceInlineForDebate]
    autocomplete_fields = ['attendance1', 'attendance2']

    def has_add_permission(self, request, obj=None):
        return False


    def get_readonly_fields(self, request, obj):
        if obj.match_day.date != timezone.localdate():
            return ("attendance1", "attendance2", 'judges')
        else:
            return tuple()

    def save_model(self, request, obj, form, change):
        
        super().save_model(request, obj, form, change)

        # Update team judged_before
        for judge in obj.judges.all():
            if not judge.team.judged_before:
                Team.objects.filter(pk=judge.team.id).update(judged_before=True)

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
    list_display = ("name", "team", "qualification_score")
    list_filter = ("team",)

class MyScoreAdmin(admin.ModelAdmin):
    list_display = ('speaker', 'debate')

    def has_add_permission(self, request, obj=None):
        return False


class MyAttendanceAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "team", "count_qualified_judges")
    list_filter = ("timestamp", "team")

    # Allow search for attendances by team name
    ordering = ['-timestamp']
    search_fields = ['team__name']

    def has_add_permission(self, request, obj=None):
        return False

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        queryset = queryset.filter(timestamp__date=timezone.localdate())
        return queryset, use_distinct


class MyMatchDayAdmin(admin.ModelAdmin):
    inlines = [DebateInstanceInline]
    readonly_fields = ["date"]
    fields = ('date',)

class MyAdminSite(admin.AdminSite):
    site_header = "UQ Debating Society Internals Administration"
    site_title = "UQDS Admin"


admin_site = MyAdminSite(name="myadmin")
admin_site.register(Team, MyTeamAdmin)
admin_site.register(Speaker, MySpeakerAdmin)
admin_site.register(Attendance, MyAttendanceAdmin)
admin_site.register(Score, MyScoreAdmin)
admin_site.register(Debate, MyDebateAdmin)
admin_site.register(MatchDay, MyMatchDayAdmin)