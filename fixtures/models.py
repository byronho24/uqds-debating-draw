from django.db import models


class Team(models.Model):

    team_name = models.CharField(max_length=200, unique=True)
    wins = models.IntegerField(default=0)
    judged_before = models.BooleanField(default=False)

    def __str__(self):
        return self.team_name


class Speaker(models.Model):

    name = models.CharField(max_length=50, unique=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    state_team = models.BooleanField(default=False)
    pro = models.BooleanField(default=False)
    easters_attend = models.BooleanField(default=False)
    easters_break = models.BooleanField(default=False)
    australs_break = models.BooleanField(default=False)
    awdc_break = models.BooleanField(default=False)
    wudc_break = models.BooleanField(default=False)

    def __str__(self):
        return self.name
