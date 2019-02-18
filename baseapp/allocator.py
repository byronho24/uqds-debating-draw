from .models import Attendance, Speaker, Team, Debate, MatchDay
from django.utils import timezone
from typing import List
import math
from operator import itemgetter, attrgetter
from .exceptions import NotEnoughJudgesException, CannotFindWorkingConfigurationException, NotEnoughAttendancesException

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

# FIXME: algo would end up always having most qualified teams to judge?
# FIXME: sometimes would end up that we have enough qualified judges but the team with the qualified judges aren't ranked top
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

    print(attendance.team.name, score)
    return score

def _number_of_debates(attendances: List[Attendance]):
    return math.floor(len(attendances) / 2)

def get_qualified_judges(attendances_judging):
    """
    Returns the qualified judges within the attendances given.
    """
    qualified_judges = []
    for attendance in attendances_judging:
        for judge in attendance.speakers.all():
            if judge.is_qualified_as_judge():
                qualified_judges.append(judge)
    return qualified_judges

def get_vetoed_speakers_for_attendance(attendance: Attendance):
    vetoed_speakers = []
    for speaker in attendance.speakers.all():
        for vetoed_speaker in speaker.vetoes.all():
            vetoed_speakers.append(vetoed_speaker)
    return vetoed_speakers

def is_vetoed(initiator: Attendance, receiver: Attendance):
    """
        Returns True if any speaker in 'initiator' has vetoed any speaker in 'receiver'.
        Return False otherwise.
    """
    initiator_vetoed_speakers = get_vetoed_speakers_for_attendance(initiator)
    for speaker in receiver.speakers.all():
        if speaker in initiator_vetoed_speakers:
            return True
    return False

def find_first_non_vetoed_attendance_in_debate(initiator: Attendance, debate: Debate):
    """
    Finds the first attendance in 'debate' that 'initiator' has not vetoed, and returns it.
    debate.attendance1 comes first, compared to debate.attendance2.
    Returns None if no such attendance can be found in the 'debate' given.
    """
    for attendance in [debate.attendance1, debate.attendance2]:
        if not is_vetoed(initiator, attendance):
            return attendance
    return None


def find_attendance_to_swap(attendance_to_swap: Attendance, debate_choices: List[Debate]):
    """
    This function is for veto purposes.
    Finds the earliest attendance in the debates in 'debate_choices' that 'attendance_to_swap' has not vetoed.
    Returns a tuple that contains (in this order): 
        - the debate that the found attendance is in
        - a string, either 'attendance1' or 'attendance2', that signifies which of the attendances in the debate
          is the found attendance

    debate.attendance1 comes before debate.attendance2.
    If no such attendance can be found, returns None.
    """
    for debate in debate_choices:
        attendance_available = find_first_non_vetoed_attendance_in_debate(attendance_to_swap, debate)
        if attendance_available is not None:
            return (debate, attendance_available)

    # If function has not returned yet, then no attendance can be found to swap with 'attendance_to_swap'
    return None      

def _assign_competing_teams(attendances: List[Attendance]):
    """
    Determines which teams are competing and the speakers that will be judging on the day.

    :param attendances: Attendances to be assigned competitions to
    :return: the generated MatchDay
    :ensures: - list of competing attendances have an even number amount of elements and is non-zero
              - len(judges) >= floor(len(attendances_competing) / 2)
    """
    # Check if we have at least 3 attendances --> minimum amount for a debate with judge
    if len(attendances) < 3:
        raise NotEnoughAttendancesException("Not enough attendances to generate at least one debate.")

    # print("Want to judge")
    # for attendance in Attendance.objects.filter(want_to_judge=True, date=datetime.today()).all():
    #     for speaker in attendance.speakers.all():
    #         print(speaker)
    attendances_judging = []
    qualified_judges = 0

    # Sort teams based on judging score
    attendances = sorted(attendances, key=_assign_team_judging_score, reverse=True)
    # print(attendances)

    # Pop until we have enough qualified judges or we have no teams left
    while (qualified_judges <  _number_of_debates(attendances) or len(attendances) % 2 != 0) and len(attendances) > 0:
        indexToRemove = 0
        delta = _number_of_debates(attendances) - qualified_judges
        attendances_count = len(attendances)
        if attendances_count % 2 != 0 and delta <= 3:
            # In this case we may be able to only pop one more team from PQ
            # Seek forward to see which team (if any) matches required number of qualified judges
            SEEK_FORWARD = 2
            for i in range(0, min(SEEK_FORWARD, attendances_count)):
                attendance = attendances[i]
                if count_qualified_judges(attendance) == delta:
                    indexToRemove = i
                    break
        # Remove item at indexToRemove from PQ (defaults to 0, but if seek forward finds a better match this would be non-zero)
        judging_attendance = attendances.pop(indexToRemove)
        attendances_judging.append(judging_attendance)
        for judge in judging_attendance.speakers.all():
            if judge.is_qualified_as_judge():
                qualified_judges += 1

    # print(f"Debates: { _number_of_debates(attendances)}")
    # print(f"Judges: {judges}")
    # print(f"Qualified judges: {len(qualified_judges)}")

    # Check if assigning process gave valid results
    if not attendances:
        raise NotEnoughJudgesException("Not enough qualified judges to host debates.")

    # Assigning process gives valid result - now save to new MatchDay instance
    match_day = MatchDay()
    match_day.save()
    for attendance in attendances:
        match_day.attendances_competing.add(attendance)
    for attendance_judging in attendances_judging:
        match_day.attendances_judging.add(attendance_judging)
    match_day.save()

    return match_day
    

def _matchmake(match_day: MatchDay):
    """
    Assigns the debates for the day.

    :param match_day: the MatchDay to generate debates for
    :return: the generated MatchDay
    :requires:  - len(attendances_competing) is greater than zero and even
                - len(judges) >= floor(len(attendances) / 2)

    """
    # Clear any existing debates for the day
    Debate.objects.filter(match_day=match_day).delete()

    attendances_competing = list(match_day.attendances_competing.all())
    judges = get_qualified_judges(match_day.attendances_judging.all())

    sorting_list = []
    for attendance in attendances_competing:
        team = attendance.team
        sorting_list.append((team.get_wins(), team.get_speakers_avg_score(), attendance))
    # Sort teams by wins then by average speaker score
    sorting_list.sort(key=itemgetter(0, 1), reverse=True)
    attendances_competing = [item[2] for item in sorting_list]

    debates = []
    number_of_debates = _number_of_debates(attendances_competing)
    # Generate the debate objects
    for i in range(0, number_of_debates):
        attendance1 = attendances_competing[i*2]
        attendance2 = attendances_competing[i*2 + 1]

        debate = Debate()
        debate.match_day = match_day
        debate.attendance1 = attendance1
        debate.attendance2 = attendance2
        debate.save() # For ManyToManyRelation

        # Assign judges - do this circularly (i.e. if there are excess judges
        # assign to higher ranked debates in order)
        judge_indices = range(i, len(judges), number_of_debates)
        for judge_index in judge_indices:
            debate.judges.add(judges[judge_index])
        debate.save()
        debates.append(debate)

    # Check for vetoes
    # The reason to use another for loop is to make sure that all the debates
    # are generated beforehand, so that if the algorithm can't find a working
    # solution in the end, at least it can give a partially working one
    for i, debate in enumerate(debates):
        attendance1 = debate.attendance1
        attendance2 = debate.attendance2

        if is_vetoed(attendance1, attendance2) or is_vetoed(attendance2, attendance1):
            # Swap attendance2 (since it is lower ranked) with the highest ranked non-vetoed
            # attendance ranked below
            debates_below = [debates[j] for j in range(i+1, len(debates))]
            swap_details = find_attendance_to_swap(attendance2, debates_below)
            if swap_details is not None:
                debate_to_swap, attendance_attr = swap_details
                # Swap debate.attendance2 with attendace_to_swap
                debate.attendance2 = getattr(debate_to_swap, attendance_attr)
                if attendance_attr == "attendance1":
                    debate_to_swap.attendance1 = attendance2 
                elif attendance_attr == "attendance2":
                    debate_to_swap.attendance2 = attendance2
            else:
                # No available attendance to swap with - raise exception for now
                raise CannotFindWorkingConfigurationException(
                    "Cannot allocate debates that satisfy veto criteria - please allocate debates manually."
                )
                # TODO: use a status code instead?

    return match_day

def generate_debates(attendances: List[Attendance]):
    """
    Generates debates given the list of attendances for the day.
    Instantiates Debate objects and saves them to the database.

    :param attendances: Attendances to generate debates for
    :return: the generated MatchDay
    """
    if not attendances:
        return []   # No attendances
    match_day = _matchmake(_assign_competing_teams(attendances))
    return match_day