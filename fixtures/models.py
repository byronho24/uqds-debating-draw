from django.db import models


class Team(models.Model):

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
    team = models.ForeignKey(Team, on_delete=models.CASCADE) # TODO: fix cascade
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
        score += state_team * WEIGHTS['StateTeam'] + \
                 pro * WEIGHTS['Pro'] + \
                 easters_attend * WEIGHTS['EastersAttend'] + \
                 easters_break * WEIGHTS['EastersBreak'] + \
                 australs_break * WEIGHTS['AustralsBreak'] + \
                 awdc_break * WEIGHTS['AWDCBreak'] + \
                 wudc_break * WEIGHTS['WUDCBreak']
        return score > self.JUDGE_THRESHOLD


class Attendance(models.Model):

    timestamp = models.DateTimeField('timestamp')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    want_to_judge = models.BooleanField(default=True)
    speakers = models.ManyToManyField(Speaker)
