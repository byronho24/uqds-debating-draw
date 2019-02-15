from django.db import models
from datetime import datetime, timedelta, tzinfo
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS

# TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT = '%Y-%m-%d'

class Team(models.Model):

    MAX_SPEAKERS = 5

    name = models.CharField(max_length=200, unique=True)
    judged_before = models.BooleanField(default=False)
    wins = models.IntegerField(default=0)

    def get_speakers_avg_score(self):
        avg = 0
        speakers = self.speaker_set.all()
        if not speakers:
            return avg  # No speakers in team yet
        for speaker in speakers:
            avg += speaker.get_avg_score()
        avg /= len(speakers)
        return avg

    def count_qualified_judges(self):
        return sum(1 for speaker in self.speaker_set.all() if speaker.is_qualified_as_judge())

    def __str__(self):
        return self.name


class Speaker(models.Model):

    JUDGE_THRESHOLD = 10

    WEIGHTS = {
        'StateTeam': 10,
        'Pro': 30,
        'EastersAttend': 5,
        'EastersBreak': 10,
        'AustralsBreak': 20,
        'AWDCBreak': 10,
        'WUDCBreak': 100
    }

    name = models.CharField(max_length=50)
    team = models.ForeignKey(Team, blank=True, null=True,
    on_delete=models.SET_NULL)
    state_team = models.BooleanField(default=False)
    pro = models.BooleanField(default=False)
    easters_attend = models.BooleanField(default=False)
    easters_break = models.BooleanField(default=False)
    australs_break = models.BooleanField(default=False)
    awdc_break = models.BooleanField(default=False)
    wudc_break = models.BooleanField(default=False)
    judge_qualification_score = models.IntegerField(editable=False, default=0)

    def __str__(self):
        return self.name

    def get_avg_score(self):
        avg = 0
        scores = self.score_set.all()
        if not scores:
            return avg  # No scores yet
        for score in scores:
            avg += score.score
        avg /= len(scores)
        return avg

    def _get_judge_qualification_score(self) -> int:
        score = 0
        score += self.state_team * self.WEIGHTS['StateTeam'] + \
                 self.pro * self.WEIGHTS['Pro'] + \
                 self.easters_attend * self.WEIGHTS['EastersAttend'] + \
                 self.easters_break * self.WEIGHTS['EastersBreak'] + \
                 self.australs_break * self.WEIGHTS['AustralsBreak'] + \
                 self.awdc_break * self.WEIGHTS['AWDCBreak'] + \
                 self.wudc_break * self.WEIGHTS['WUDCBreak']
        return score

    def save(self, *args, **kwargs):
        self.judge_qualification_score = self._get_judge_qualification_score()
        super().save(*args, **kwargs)

    def is_qualified_as_judge(self):
        return self.judge_qualification_score >= self.JUDGE_THRESHOLD


class Attendance(models.Model):

    timestamp = models.DateTimeField('timestamp', default=timezone.now)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    speakers = models.ManyToManyField(Speaker)
    want_to_judge = models.BooleanField(default=False)

    def count_qualified_judges(self):
        return sum(1 for speaker in self.speakers.all() if speaker.is_qualified_as_judge())

    def __str__(self):
        return f"{self.timestamp.strftime(TIME_FORMAT)}  {self.team.name}"


class Debate(models.Model):
    date = models.DateField(default=timezone.localdate)
    attendance1 = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name="attendance1_debate")
    attendance2 = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name="attendance2_debate")
    judge = models.ForeignKey(Speaker, null=True, on_delete=models.SET_NULL)
    winning_team = models.ForeignKey(Team, null=True, blank=False,
                                        default=None, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.date}"

    def get_attendances(self):
        return [self.attendance1, self.attendance2]

    def clean(self):
        # Do not allow save if attendance1 == attendance2
        if self.attendance1 == self.attendance2:
            raise ValidationError(_('Attendance1 must be different to attendance2.'))
        # Do not allow save if attendances are not in the same day
        if self.attendance1.timestamp.date() != self.date or \
                self.attendance2.timestamp.date() != self.date:
            raise ValidationError(_("Date of attendances must match debate's date."))


# class MatchDay(models.Model):
#     """ Saves the attentances that are competing and the 
#         speakers assigned to be judges on the day."""
#     date = models.DateField()
#     attendances_competing = models.ManyToManyField(Attendance)
#     judges = models.ManyToManyField(Speaker)


class Score(models.Model):

    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=2, decimal_places=1, blank=False,
                                    validators=[
                                        MaxValueValidator(10),
                                        MinValueValidator(1)
                                    ])
    debate = models.ForeignKey(Debate, on_delete=models.CASCADE)
