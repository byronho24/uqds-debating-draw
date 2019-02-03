from django.db import models
from datetime import datetime, timedelta, tzinfo
from django.core.validators import MinValueValidator, MaxValueValidator

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def _local_time_now():
    # FIXME: timezone conversion hardcoded for now - tried to implement the
    # tzinfo class (as you can see below ) but for some reason it didn't work
    return datetime.utcnow() + timedelta(hours=10)

class Australia_Brisbane(tzinfo):
    """ Timezone for Australia/Brisbane """
    def utcoffset(self, dt):
        return timedelta(hours=10)

    def tzname(self, dt):
        return "Australia/Brisbane"

    def dst(self, dt):
        return timedelta(0)

class Team(models.Model):

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

    name = models.CharField(max_length=50, unique=True)
    team = models.ForeignKey(Team, blank=True, null=True,
    on_delete=models.SET_NULL)
    state_team = models.BooleanField(default=False)
    pro = models.BooleanField(default=False)
    easters_attend = models.BooleanField(default=False)
    easters_break = models.BooleanField(default=False)
    australs_break = models.BooleanField(default=False)
    awdc_break = models.BooleanField(default=False)
    wudc_break = models.BooleanField(default=False)

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

    def is_qualified_as_judge(self) -> bool:
        score = 0
        score += self.state_team * self.WEIGHTS['StateTeam'] + \
                 self.pro * self.WEIGHTS['Pro'] + \
                 self.easters_attend * self.WEIGHTS['EastersAttend'] + \
                 self.easters_break * self.WEIGHTS['EastersBreak'] + \
                 self.australs_break * self.WEIGHTS['AustralsBreak'] + \
                 self.awdc_break * self.WEIGHTS['AWDCBreak'] + \
                 self.wudc_break * self.WEIGHTS['WUDCBreak']
        return score > self.JUDGE_THRESHOLD


class Debate(models.Model):
    date = models.DateField()
    judge = models.ForeignKey(Speaker, null=True, on_delete=models.SET_NULL)
    winning_team = models.ForeignKey(Team, null=True, blank=False,
                                        default=None, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.date}"


class Attendance(models.Model):

    timestamp = models.DateTimeField('timestamp', default=_local_time_now)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    speakers = models.ManyToManyField(Speaker)
    want_to_judge = models.BooleanField(default=True)
    debate = models.ForeignKey(Debate, null=True, on_delete=models.SET_NULL, default=None)


    def __str__(self):
        return f"{self.timestamp.strftime(TIME_FORMAT)}  {self.team.name}"

class Score(models.Model):

    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=2, decimal_places=1, blank=False,
                                    validators=[
                                        MaxValueValidator(10),
                                        MinValueValidator(1)
                                    ])
    debate = models.ForeignKey(Debate, on_delete=models.CASCADE)
