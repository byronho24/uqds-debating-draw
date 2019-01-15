from django.db import models
from datetime import datetime, timedelta
from pytz import timezone

LOCAL_TIMEZONE = timezone('Australia/Brisbane')
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def _local_time_now():
    local_time = datetime.utcnow().astimezone(LOCAL_TIMEZONE)
    return local_time

class Team(models.Model):

    MAXIMUM_SIZE = 5

    team_name = models.CharField(max_length=200, unique=True)
    wins = models.IntegerField(default=0)
    judged_before = models.BooleanField(default=False)

    def __str__(self):
        return self.team_name


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


class Attendance(models.Model):


    timestamp = models.DateTimeField('timestamp', default=_local_time_now)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    speakers = models.ManyToManyField(Speaker)
    want_to_judge = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.timestamp.strftime(TIME_FORMAT)}  {self.team.team_name}"
