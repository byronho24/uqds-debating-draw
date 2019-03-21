from django.contrib import admin

from .models import Team, Speaker, Attendance, Debate, Score, MatchDay, Veto, Room
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
        if obj:
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
    # autocomplete_fields = ["affirmative", "negative"]
    show_change_link = True
    # form = make_ajax_form(Debate, {
    #     'affirmative': 'attendances_for_debate',
    #     'negative': 'attendances_for_debate',
    #     'judges': 'judges_for_debate'
    # })

    def get_max_num(self, request, obj=None, **kwargs):
        if obj and obj.date != timezone.localdate():
            return Debate.objects.filter(match_day=obj).count()
        else:
            return super().max_num

    def get_readonly_fields(self, request, obj):
        if obj and obj.date != timezone.localdate():
            return ("affirmative", "negative", 'judges')
        else:
            return tuple()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "affirmative" or db_field.name == "negative":
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
                # Empty Speaker queryset
                # FIXME: this looks like a hack more than anything hahaha.
                qs = Speaker.objects.filter(id=0).all()
                for attendance_judging in match_day.attendances_judging.all():
                    qs |= attendance_judging.speakers.all()
                kwargs["queryset"] = qs
            except MatchDay.DoesNotExist:
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
    list_display = ("name", "wins")
    # list_filter = ("wins",)
    inlines = [SpeakerInstanceInline]

    def wins(self, obj):
        return obj.get_wins()
    wins.admin_order_field = '-debates_won'


    def has_add_permission(self, request, obj=None):
        return False


class MyDebateAdmin(admin.ModelAdmin):
    list_display = (
        'match_day', 'affirmative', 'negative'
    )
    list_filter = ('match_day',)
    # list_editable = (
    #     'affirmative', 'negative', 'judges',
    # )
    inlines = [ScoreInstanceInlineForDebate]
    # autocomplete_fields = ['affirmative', 'negative']

    def has_add_permission(self, request, obj=None):
        return False


    def get_readonly_fields(self, request, obj):
        if obj.match_day.date != timezone.localdate():
            return ("affirmative", "negative", 'judges')
        else:
            return tuple()

    def save_model(self, request, obj, form, change):
        
        super().save_model(request, obj, form, change)

        # Update team judged_before
        if obj:
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
    list_display = ("name", "team", "qualification_score", "get_avg_score")
    list_filter = ("team",)

    # Allow search for speakers by name
    search_fields = ('name',)
    ordering = ('name',)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


class MyScoreAdmin(admin.ModelAdmin):
    list_display = ('speaker', 'debate')

    def has_add_permission(self, request, obj=None):
        return False


class MyAttendanceAdmin(admin.ModelAdmin):
    list_display = ("date", "team", "count_qualified_judges")
    list_filter = ("date", "team")

    # # Allow search for attendances by team name
    # ordering = ['-date']
    # search_fields = ['team__name']

    def has_add_permission(self, request, obj=None):
        return False

    # def get_search_results(self, request, queryset, search_term):
    #     queryset, use_distinct = super().get_search_results(request, queryset, search_term)
    #     queryset = queryset.filter(date=timezone.localdate())
    #     return queryset, use_distinct


class MyMatchDayAdmin(admin.ModelAdmin):
    inlines = [DebateInstanceInline]
    fields = ('date', 'attendances_competing', 'attendances_judging')
    def get_readonly_fields(self, request, obj):
        if obj and obj.date != timezone.localdate():
            return ('date', 'attendances_judging', 'attendances_competing')
        else:
            return ('date',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "attendances_competing" or db_field.name == "attendances_judging":
            kwargs["queryset"] = Attendance.objects.filter(date=timezone.localdate())
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class MyVetoAdmin(admin.ModelAdmin):
    autocomplete_fields = ('initiator', 'receiver')
    list_display = ('initiator', 'receiver', 'affected_debates')
    list_display_links = ('initiator', 'receiver')


class MyRoomAdmin(admin.ModelAdmin):
    list_display = ('date', 'name')
    list_filter = ('date',)

class MyAdminSite(admin.AdminSite):
    site_header = "UQ Debating Society Internals Administration"
    site_title = "UQDS Admin"

    def get_app_list(self, request):
        ordering = {
            'Teams': 1,
            'Speakers': 2,
            'Attendances': 3,
            'Rooms': 4,
            'Draws': 5,
            'Debates': 6,
            'Vetos': 7
        }
        app_dict = self._build_app_dict(request)
        # Sort apps alphabetically
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

        # Sort models within baseapp using custom ordering
        for app in app_list:
            if app['name'] == 'baseapp':
                app['models'].sort(key=lambda x: ordering[x['name']])
                break
        
        return app_list

admin_site = MyAdminSite(name="myadmin")
admin_site.register(Team, MyTeamAdmin)
admin_site.register(Speaker, MySpeakerAdmin)
admin_site.register(Attendance, MyAttendanceAdmin)
admin_site.register(MatchDay, MyMatchDayAdmin)
admin_site.register(Debate, MyDebateAdmin)
admin_site.register(Veto, MyVetoAdmin)
admin_site.register(Room, MyRoomAdmin)

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
admin_site.register(Group, GroupAdmin)
admin_site.register(User, UserAdmin)