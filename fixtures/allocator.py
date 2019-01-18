from .models import Attendance, Speaker, Team
from typing import List
import math
from operator import itemgetter


# Weightings
WEIGHTS = {
    'never_judged': 6,
    'want_to_judge': 3,
    'two_present': 4,
    'one_present': 12
}

def _assign_judging_score(attendance: Attendance):
    # Get data from attendance
    number_attending = len(attendance.speakers.all())
    never_judged = not attendance.team.judged_before
    want_to_judge = attendance.want_to_judge

    # Assign score
    score = never_judged *  WEIGHTS["never_judged"] + \
        want_to_judge * WEIGHTS["want_to_judge"]
    if number_attending == 1:
        score += WEIGHTS["one_present"]
    elif number_attending == 2:
        score += WEIGHTS["two_present"]

    return score

def number_of_debates(attendances: List[Attendance]):
    return math.floor(len(attendances) / 2)

def assign_competing_teams(attendances: List[Attendance]):
    """
    Determines which teams are competing and which teams are judging on the day.

    :param attendances: Attendances to be assigned competitions to
    :return: tuple of (list of competing attendances, list of speakers judging)
    """
    # FIXME: algo to account for qualified judges
    judges = []

    # Sort teams based on judging score
    attendances = sorted(attendances, key=_assign_judging_score, reverse=True)

    # Pop until we have enough judges
    while len(judges) <  number_of_debates(attendances) or len(attendances) % 2 != 0 :
        # Pop one team
        judging_attendance = attendances.pop(0)
        for judge in judging_attendance.speakers.all():
            judges.append(judge)

    # TODO: for teams that are judging, set their judged_before to True
    # Or do we do that after the match?
    return ([attendance for attendance in attendances], judges)

def matchmake(attendances_competing: List[Attendance], judges: List[Speaker]):
    """
    Assigns the debates for the day.

    :param attendances_competing: Attendances to assign competitions for
    :param judges: Available judges for the day
    :return: List of (attendance1, attendance2, judge) tuples representing the
    debates that are assigned

    """
    sorting_list = []
    for attendance in attendances_competing:
        team = attendance.team
        sorting_list.append((team.wins, team.get_speakers_avg_score(), attendance))
    # Sort teams by wins then by average speaker score
    sorting_list.sort(key=itemgetter(0, 1), reverse=True)
    attendances_competing = [item[2] for item in sorting_list]
    debates = []

    for i in range(0, number_of_debates(attendances_competing)):
        # Return list of tuples indicating the pairs of competing teams and assign a judge
        debates.append((attendances_competing[i*2],
                        attendances_competing[i*2+1],
                        judges[i]))

    return debates
