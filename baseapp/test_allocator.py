from django.test import TestCase
from .models import Speaker, Attendance, Team, MatchDay, Score
from .allocator import generate_debates
import random 

ATTENDACES_PER_MATCHDAY_AVG = 20
PROB_PREFER_TO_JUDGE = 0.15
DELTA_PROB_WIN_PER_WIN_DELTA = 0.1

def generate_attendance(date, team):
    speakers_count = team.speaker_set.count()
    if speakers_count >= 3:
        attending_speakers_count = random.randint(2, 3)
    else:
        attending_speakers_count = random.randint(1, 2)
    attending_speakers = random.sample(list(team.speaker_set.all()), min(attending_speakers_count, speakers_count))
    prefer_to_judge = random.choice([True] * (int(100 * PROB_PREFER_TO_JUDGE)) + \
                                        [False] * int(100 * (1 - PROB_PREFER_TO_JUDGE)))
    
    # Create attendance
    attendance = Attendance()
    attendance.date = date
    attendance.team = team
    attendance.save()
    attendance.speakers.set(attending_speakers)
    attendance.want_to_judge = prefer_to_judge
    attendance.save()

    return attendance

def generate_attendances(date):
    attendances_count = random.randint(ATTENDACES_PER_MATCHDAY_AVG - 2, ATTENDACES_PER_MATCHDAY_AVG + 2)
    teams = list(Team.objects.all())
    teams_attending = random.sample(teams, min(attendances_count, len(teams)))
    attendances = []
    for team in teams_attending:
        # Generate attendance
        attendance = generate_attendance(date, team)
        attendances.append(attendance)
    return attendances

def generate_debate_results(debate):
    affirmative_team = debate.affirmative.team
    negative_team = debate.negative.team
    win_delta = affirmative_team.get_wins() - negative_team.get_wins()

    aff_win_prob = 0.5 + win_delta * DELTA_PROB_WIN_PER_WIN_DELTA
    if aff_win_prob > 1:
        aff_win_prob = 1
    elif aff_win_prob < 0:
        aff_win_prob = 0
    neg_win_prob = 1 - aff_win_prob
    winning_team = random.choice([affirmative_team] * int(100 * aff_win_prob) + \
                                        [negative_team] * int(100 * neg_win_prob))
    
    from decimal import Decimal
    for speaker in winning_team.speaker_set.all():
        # New score object
        score = random.randint(9,10)
        Score.objects.create(debate=debate, speaker=speaker, score=score)
    
    losing_team = next(team for team in [affirmative_team, negative_team] if team != winning_team)
    for speaker in losing_team.speaker_set.all():
        score = random.randint(7,8)
        Score.objects.create(debate=debate, speaker=speaker, score=score)
    
    debate.winning_team = winning_team
    debate.save()
    return debate

def simulate_rounds(count):
    from datetime import timedelta
    from django.utils import timezone
    today = timezone.localdate()
    
    # Clear data from previous simulations
    MatchDay.objects.filter(date__gt=today).delete()
    Attendance.objects.filter(date__gt=today).delete()

    match_days = []
    for i in range(0, count):
        date = today + timedelta(days=i+1)
        generate_attendances(date)
        # Generate debates
        match_day = generate_debates(date, ignore_rooms=True)
        # Generate debate results
        for debate in match_day.debate_set.all():
            generate_debate_results(debate)
        match_days.append(match_day)
    return match_days