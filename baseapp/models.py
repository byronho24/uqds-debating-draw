from django.db import models
from datetime import datetime, timedelta, tzinfo
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS

# TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT = '%Y-%m-%d'

class Team(models.Model):

    MAX_SPEAKERS = 5

    name = models.CharField(max_length=200, unique=True, verbose_name="Team Name")
    judged_before = models.BooleanField(default=False)

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

    def get_wins(self):
        return self.debates_won.count()

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
    qualification_score = models.IntegerField(editable=False, default=0)
    vetoes = models.ManyToManyField('self', symmetrical=False)

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

    def _get_qualification_score(self) -> int:
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
        self.qualification_score = self._get_qualification_score()
        super().save(*args, **kwargs)

    def is_qualified_as_judge(self):
        return self.qualification_score >= self.JUDGE_THRESHOLD


class Attendance(models.Model):

    date = models.DateField(default=timezone.localdate)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    speakers = models.ManyToManyField(Speaker)
    want_to_judge = models.BooleanField(default=False, verbose_name="prefer to judge")

    def count_qualified_judges(self):
        return sum(1 for speaker in self.speakers.all() if speaker.is_qualified_as_judge())

    def __str__(self):
        return f"{self.date}  {self.team.name}"


class Debate(models.Model):
    match_day = models.ForeignKey('MatchDay', on_delete=models.CASCADE, null=True)
    affirmative = models.ForeignKey(Attendance, verbose_name="Affirmative team", on_delete=models.CASCADE, related_name="debates_affirmative", null=True)
    negative = models.ForeignKey(Attendance, verbose_name="Negative team", on_delete=models.CASCADE, related_name="debates_negative", null=True)
    judges = models.ManyToManyField(Speaker)
    winning_team = models.ForeignKey(Team, null=True, blank=False,
                                        default=None, on_delete=models.CASCADE,
                                            related_name="debates_won")
    
    def __str__(self):
        return f"{self.match_day}"

    def get_attendances(self):
        return [self.affirmative, self.negative]

    def clean(self):
        # Do not allow save if affirmative == negative
        if self.affirmative == self.negative:
            raise ValidationError('Debate must be held between two different teams.')
        # Do not allow save if attendances are not in the same day
        if self.affirmative.date != self.match_day.date or \
                self.negative.date != self.match_day.date:
            raise ValidationError("Date of attendances must match debate's date.")


class MatchDay(models.Model):
    """ Saves the debates for a specific match day."""
    date = models.DateField(default=timezone.localdate, unique=True)
    attendances_competing = models.ManyToManyField(Attendance, related_name="competing_matchdays")
    attendances_judging = models.ManyToManyField(Attendance, related_name="judging_matchdays")

    def __str__(self):
        return f"{self.date}"

class Score(models.Model):

    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=2, decimal_places=1, blank=False,
                                    validators=[
                                        MaxValueValidator(10),
                                        MinValueValidator(1)
                                    ])
    debate = models.ForeignKey(Debate, on_delete=models.CASCADE)
