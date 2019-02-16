from .models import Attendance, Speaker, Team, Debate
from datetime import datetime
from typing import List
import math
from operator import itemgetter, attrgetter
from .exceptions import NotEnoughJudgesException, CannotFindWorkingConfigurationException

# Weightings
WEIGHTS = {
    'never_judged': 6,
    'want_to_judge': 3,
    'two_present': 4,
    'one_present': 12,
    'qualified_judge': 4
}

def count_qualified_judges(attendance: Attendance):
    sum(1 for speaker in attendance.speakers.all() if speaker.is_qualified_as_judge())


def _assign_team_judging_score(attendance: Attendance):
    # Get data from attendance
    number_attending = len(attendance.speakers.all())
    never_judged = not attendance.team.judged_before
    want_to_judge = attendance.want_to_judge
    number_of_qualified_judges = attendance.count_qualified_judges()

    # Assign score
    score = never_judged *  WEIGHTS["never_judged"] + \
            want_to_judge * WEIGHTS["want_to_judge"] + \
            number_of_qualified_judges * WEIGHTS["qualified_judge"]
    if number_attending == 1:
        score += WEIGHTS["one_present"]
    elif number_attending == 2:
        score += WEIGHTS["two_present"]

    return score

def _number_of_debates(attendances: List[Attendance]):
    return math.floor(len(attendances) / 2)

def get_vetoed_speakers_for_attendance(attendance: Attendance):
    vetoed_speakers = []
    for speaker in attendance.speakers.all():
        for vetoed_speaker in speaker.vetoes.all():
            vetoed_speakers.append(vetoed_speaker)
    return vetoed_speakers

def is_vetoed(attendance1: Attendance, attendance2: Attendance):
    """
        Returns True if any speaker of attendance1 has vetoed any speaker in attendance2.
        Return False otherwise.
    """
    attendance1_vetoed_speakers = get_vetoed_speakers_for_attendance(attendance1)
    for speaker in attendance2.speakers.all():
        if speaker in attendance1_vetoed_speakers:
            return True
    return False

def _assign_competing_teams(attendances: List[Attendance]):
    """
    Determines which teams are competing and which teams are judging on the day.

    :param attendances: Attendances to be assigned competitions to
    :return: tuple of (list of competing attendances, list of speakers judging)
    :ensures: list of competing attendances have an even number amount of elements
    """
    # Check if multiple Attendance entries exist for any given attending team
    # If so only consider the most recent entry
    attendances = sorted(attendances, key=attrgetter('timestamp'))
    attendances_dict = {}
    for attendance in attendances:
        # Write into dictionary with team id as key - most recent entry for a
        # given team would overwrite its previous attendance entries
        attendances_dict[attendance.team.id] = attendance
    attendances = list(attendances_dict.values())

    # print("Want to judge")
    # for attendance in Attendance.objects.filter(want_to_judge=True, timestamp__date=datetime.today()).all():
    #     for speaker in attendance.speakers.all():
    #         print(speaker)
    # FIXME: algo to account for qualified judges
    qualified_judges = []
    judges = 0

    # Sort teams based on judging score
    attendances = sorted(attendances, key=_assign_team_judging_score, reverse=True)

    # Pop until we have enough qualified judges or we have no teams left
    while (len(qualified_judges) <  _number_of_debates(attendances) or len(attendances) % 2 != 0) and len(attendances) > 0:
        indexToRemove = 0
        delta = _number_of_debates(attendances) - len(qualified_judges)
        attendances_count = len(attendances)
        if attendances_count % 2 != 0 and delta <= 3:
            # In this case we may be able to only pop one more team from PQ
            # Seek forward to see which team (if any) matches required number of qualified judges
            SEEK_FORWARD = 3
            for i in range(0, min(SEEK_FORWARD, attendances_count)):
                attendance = attendances[i]
                if count_qualified_judges(attendance) == delta:
                    indexToRemove = i
                    break
        # Remove item at indexToRemove from PQ (defaults to 0, but if seek forward finds a better match this would be non-zero)
        judging_attendance = attendances.pop(indexToRemove)
        for judge in judging_attendance.speakers.all():
            judges += 1
            if judge.is_qualified_as_judge():
                qualified_judges.append(judge)

    # print(f"Debates: { _number_of_debates(attendances)}")
    # print(f"Judges: {judges}")
    # print(f"Qualified judges: {len(qualified_judges)}")
    return (attendances, qualified_judges)

def _matchmake(attendances_competing: List[Attendance], judges: List[Speaker]):
    """
    Assigns the debates for the day.

    :param attendances_competing: Attendances to assign competitions for
    :param judges: Available judges for the day
    :return: QuerySet of Debate objects

    """
    # Clear any existing debates for the day
    Debate.objects.filter(date=datetime.today()).delete()
    
    if _number_of_debates(attendances_competing) > len(judges):
        raise NotEnoughJudgesException("Not enough qualified judges available")

    # TODO: account for vetoes
    sorting_list = []
    for attendance in attendances_competing:
        team = attendance.team
        sorting_list.append((team.get_wins(), team.get_speakers_avg_score(), attendance))
    # Sort teams by wins then by average speaker score
    sorting_list.sort(key=itemgetter(0, 1), reverse=True)
    attendances_competing = [item[2] for item in sorting_list]

    debates = []
    # Generate the debate objects
    for i in range(0, _number_of_debates(attendances_competing)):
        # Remove first two attendances from PQ
        attendance1 = attendances_competing.pop(0)
        attendance2 = attendances_competing.pop(0)

        # Check for vetoes --> doesn't matter who initiated the veto
        if is_vetoed(attendance1, attendance2) or is_vetoed(attendance2, attendance1):
            # Swap attendance2 (the lower ranked out of [attendance1, attendance2])
            #  with highest ranked non-vetoed team ranked below
            for attendance_to_swap in attendances_competing:
                if not is_vetoed(attendance2, attendance_to_swap):
                    # TODO: use a deque?
                    # Prepend original attendance2 back into PQ
                    attendances_competing.insert(0, attendance2)
                    # Remove attendance_to_swap from PQ
                    attendance2 = attendance_to_swap
                    attendances_competing.remove(attendance_to_swap)
                    break
            else:
                # No team found for swap!
                # For now raise an error
                raise CannotFindWorkingConfigurationException(
                    "Cannot find debates that satisfy veto criteria."
                )

        debate = Debate()
        debate.date = datetime.today()
        debate.attendance1 = attendance1
        debate.attendance2 = attendance2

        debates.append(debate)

    # Assign judges to the debates
    for i, judge in enumerate(judges):
        # Assign excess judges to the highest-ranked debates
        debates[i % len(debates)].judges.add(judge)

    return debates

def generate_debates(attendances: List[Attendance]):
    """
    Generates debates given the list of attendances for the day.
    Instantiates Debate objects and saves them to the database.

    :param attendances: Attendances to generate debates for
    :return: QuerySet of Debate objects
    """
    if not attendances:
        return []   # No attendances
    competing_attendances, judges = _assign_competing_teams(attendances)
    debates = _matchmake(competing_attendances, judges)
    return debates

# def get_or_generate_debates(attendances):
#     global attendances_last
#     if (attendances_last is None) or len(attendances) != attendances_last:
#         # Generate debates
#         print("Attendances modified - now generate debates")
#         attendances_last = len(attendances)
#         return generate_debates(list(attendances))
#     else:
#         print("No new attendances")
#         # FIXME: index out of range if attendances is an empty list
#         return Debate.objects.filter(date=attendances[0].timestamp.date()).all()