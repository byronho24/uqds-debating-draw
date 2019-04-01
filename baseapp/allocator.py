from .models import Attendance, Speaker, Team, Debate, MatchDay, Veto, Room
from django.utils import timezone
from typing import List
import math
from operator import itemgetter, attrgetter
from .exceptions import NotEnoughJudgesException, CannotFindWorkingConfigurationException, NotEnoughAttendancesException, NotEnoughRoomsException

# Weightings
WEIGHTS = {
    'never_judged': 6,
    'want_to_judge': 3,
    'two_present': 4,
    'one_present': 12,
}

def count_qualified_judges(attendance: Attendance):
    sum(1 for speaker in attendance.speakers.all() if speaker.is_qualified_as_judge())

# FIXME: algo would end up always having most qualified teams to judge?
# --> Actually maybe not - since we take into account never_judged
def assign_judging_priority(attendance: Attendance):
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

def rank_attendances(attendances_competing):
    """ 
    Returns a new list of attendances, where the attendances are ranked by
    the attendance's team's number of wins in the tournament in descending order, 
    then by the attendance's team's speakers' average score for the past debates 
    in the tournament, in descending order.

    Original list 'attendances_competing' is not affected.
    """
    sorting_list = []
    for attendance in attendances_competing:
        team = attendance.team
        sorting_list.append((team.get_wins(), team.get_speakers_avg_score(), attendance))
    # Sort teams by wins then by average speaker score
    sorting_list.sort(key=itemgetter(0, 1), reverse=True)
    return [item[2] for item in sorting_list]

def _number_of_debates(attendances_count: int):
    return math.floor(attendances_count / 2)

def get_qualified_judges(attendance):
    """
    Returns the qualified judges within the attendance given.
    """
    qualified_judges = []
    for judge in attendance.speakers.all():
        if judge.is_qualified_as_judge():
            qualified_judges.append(judge)
    return qualified_judges

def get_attr_for_attendance(debate: Debate, attendance: Attendance):
    """
    Returns the attribute name (either 'affirmative' or 'negative') of the given attendance
    in the debate given.
    i.e. if debate.affirmative == attendance, then this function return 'affirmative', etc.

    Raises an ValueError if given attendance is not in the given debate.
    """
    affirmative = debate.affirmative
    negative = debate.negative
    if attendance == affirmative:
        return "affirmative"
    elif attendance == negative:
        return "negative"
    else:
        raise ValueError("Given attendance is not in the given debate.")

def get_vetoed_speakers_for_attendance(attendance: Attendance):
    vetoed_speakers = []
    for speaker in attendance.speakers.all():
        initiated_vetoes = Veto.objects.filter(initiator=speaker).all()
        for veto in initiated_vetoes:
            vetoed_speakers.append(veto.receiver)
    return vetoed_speakers

def is_vetoed(initiator: Attendance, receiver: Attendance):
    """
        Returns True if any speaker in 'initiator' has initiated a veto against any speaker in 'receiver'.
        Return False otherwise.
    """
    initiator_vetoed_speakers = get_vetoed_speakers_for_attendance(initiator)
    for speaker in receiver.speakers.all():
        if speaker in initiator_vetoed_speakers:
            return True
    return False

def is_speaker_in_attendance(speaker: Speaker, attendance: Attendance):
    """ 
    Returns True if given speaker is in the given attendancee, False otherwise.
    """
    return attendance.speakers.filter(pk=speaker.pk).exists()

def get_vetoes(init_attendance: Attendance, rec_attendance: Attendance):
    """
    Finds all of the Veto instances where the initiator is a speaker in init_attendance
    and the receiver is a speaker in rec_attendance.
    Returns a list of all such Veto instances.
    Returns an empty list if no speaker in init_attendance has initiated a veto
    against any speaker in rec_attendance.
    """
    vetoes = []
    for speaker in init_attendance.speakers.all():
        vetoes_initiated = Veto.objects.filter(initiator=speaker).all()
        if vetoes_initiated:
            for veto in vetoes_initiated:
                if is_speaker_in_attendance(veto.receiver, rec_attendance):
                    vetoes.append(veto)
    return vetoes



def find_highest_ranked_non_vetoed_attendance_in_debate(initiator: Attendance, debate: Debate):
    """
    Finds the highest ranked attendance in 'debate' that 'initiator' has not vetoed.
    Returns a string, either 'affirmative' or 'negative', which indicates the corresponding attendance.
    If both teams in the debate have the same ranking, returns 'affirmative' (for now).
    Returns None if no such attendance can be found in the 'debate' given.

    :ensures: returns either 'affirmative', 'negative', or None
    """
    attendances = rank_attendances([debate.affirmative, debate.negative])
    for attendance in attendances:
        if not is_vetoed(initiator, attendance):
            return get_attr_for_attendance(debate, attendance)
    return None


def find_attendance_to_swap(attendance_to_swap: Attendance, debate_choices: List[Debate]):
    """
    This function is for veto purposes.
    Finds the highest ranked attendance in the debates in 'debate_choices' that 'attendance_to_swap' has not vetoed.
    Returns a tuple that contains (in this order): 
        - the debate that the found attendance is in
        - a string, either 'affirmative' or 'negative', that signifies which of the attendances in the debate
          is the found attendance

    If no such attendance can be found, returns None.
    """
    for debate in debate_choices:
        attendance_available = find_highest_ranked_non_vetoed_attendance_in_debate(attendance_to_swap, debate)
        if attendance_available is not None:
            return (debate, attendance_available)

    # If function has not returned yet, then no attendance can be found to swap with 'attendance_to_swap'
    return None      

def can_host_debates(attendances_competing, judges_count: int):
    """
    Returns True if both of these conditions are true:
        1. 'judge_count' is large enough to host the debates where 'attendances_competing'
        would partake in
        2. 'attendances_competing' has an even number of elements.
    Returns False otherwise.
    """
    attendances_competing_count = len(attendances_competing)
    return (judges_count >=  _number_of_debates(attendances_competing_count) \
            and attendances_competing_count % 2 == 0)

def _assign_competing_teams(attendances: List[Attendance]):
    """
    Determines which teams are competing and the speakers that will be judging given a list of Attendances.

    :param attendances: Attendances to be assigned competitions to
    :return: a tuple of (attendances competing, attendances judging)
    :ensures: - list of competing attendances have an even number amount of elements and is non-zero
              - len(judges) >= floor(len(attendances_competing) / 2)
    """
    # Check if we have at least 3 attendances --> minimum amount for a debate with judge
    if len(attendances) < 3:
        raise NotEnoughAttendancesException("Not enough attendances to generate at least one debate.")

    # Only consider attendances with at least one qualified judge when assigning judges
    qualified_attendances, unqualified_attendances = [], []
    for attendance in attendances:
        qualified_attendances.append(attendance) if get_qualified_judges(attendance) \
            else unqualified_attendances.append(attendance)
    # Sort qualified attendance based on judging score
    qualified_attendances.sort(key=assign_judging_priority, reverse=True)

    qualified_attenances_count = len(qualified_attendances)
    attendances_competing = qualified_attendances + unqualified_attendances
    attendances_judging = []
    qualified_judges_count = 0

    SEEK_FORWARD_LIMIT = 3

    # Pop until we have enough qualified judges or we have no teams left
    while (not can_host_debates(attendances_competing, qualified_judges_count)) \
            and qualified_attenances_count > 0:
        indexToRemove = 0
        delta = _number_of_debates(len(attendances_competing)) - qualified_judges_count
        if len(attendances_competing) % 2 != 0 and 0 < delta <= 3:
            # In this case we may be able to only pop one more team from PQ
            # Seek forward to see which team (if any) matches required number of qualified judges
            for i in range(1, min(SEEK_FORWARD_LIMIT, qualified_attenances_count)):
                potential_attendance = attendances_competing[i]
                if count_qualified_judges(potential_attendance) == delta:
                    indexToRemove = i
                    break
        # Remove item at indexToRemove from PQ (defaults to 0, but if seek forward finds a better match this would be non-zero)
        judging_attendance = attendances_competing.pop(indexToRemove)
        qualified_attenances_count -= 1
        attendances_judging.append(judging_attendance)
        for judge in judging_attendance.speakers.all():
            if judge.is_qualified_as_judge():
                qualified_judges_count += 1

    # Check if assigning process gave valid results
    # i.e. check if loop exited just because it has exhuasted all the qualified attendances available
    if not can_host_debates(attendances_competing, qualified_judges_count):
        return NotEnoughJudgesException("Not enough qualified judges to host debates.")

    # Result valid
    return (attendances_competing, attendances_judging)
    
    

def assign_teams_for_date(date, ignore_rooms=False):
    attendances_today = Attendance.objects.filter(date=date)
    rooms_today_count = Room.objects.filter(date=date).count()

    attendances_competing, attendances_judging = _assign_competing_teams(attendances_today)

    # Check if there are enough rooms
    if ignore_rooms and _number_of_debates(len(attendances_competing)) > rooms_today_count:
        raise NotEnoughRoomsException("Not enough rooms available for debates.")

    # Assigning process gives valid result - now save to new MatchDay instance
    match_day = MatchDay(date=today)
    match_day.save()
    match_day.attendances_competing.set(attendances_competing)
    match_day.attendances_judging.set(attendances_judging)
    match_day.save()

    return match_day

def compare_aff_neg(team: Team):
        """
        Finds the number of times the team given has been the affirmative/negative side
        in the debates in the tournament.

        Returns the affirmative count - negative count.
        """
        aff_count = Debate.objects.filter(affirmative__team=team).count()
        neg_count = Debate.objects.filter(negative__team=team).count()
        return aff_count - neg_count

def get_attendance_higher_aff_neg_diff(attendance1: Attendance, attendance2: Attendance):
    """
    Returns the attendance out of 'attendance1' and 'attendance2' whose team has the 
    higher affirmative_count - negative_count difference.

    If both teams have the same aff_neg difference, then returns one of the two at random.

    For the definition of the aforementioned difference, consult documentation for 
    Team.compare_aff_neg.

    :ensures: returned value is either 'attendance1' or 'attendance2'
    """
    if compare_aff_neg(attendance1.team) > compare_aff_neg(attendance2.team):
        return attendance1
    elif compare_aff_neg(attendance1.team) < compare_aff_neg(attendance2.team):
        return attendance2
    else:
        from random import randint
        return [attendance1, attendance2][randint(0,1)]

def assign_aff_neg(debate: Debate, attendance1: Attendance, attendance2: Attendance):
    """
    Assigns which of attendance1 or attendance2 would be affirmative or negative in the debate.
    """
    # Check each team's affirmative/negative diff in past debates
    # Try to make it so that each team has roughly an equal share of
    # being affirmative or negative in the tournament's debates
    if get_attendance_higher_aff_neg_diff(attendance1, attendance2) == attendance1:
        debate.negative = attendance1
        debate.affirmative = attendance2
    else:
        debate.negative = attendance2
        debate.affirmative = attendance1
    
    return debate


def is_debated_before(team1: Team, team2: Team):
    qs = Debate.objects.filter(affirmative__team=team1, negative__team=team2) |\
            Debate.objects.filter(affirmative__team=team2, negative__team=team1)
    return qs.exists()

def _matchmake(match_day: MatchDay):
    """
    Assigns the debates for the day.

    :param match_day: the MatchDay to generate debates for
    :return: the generated MatchDay
    :requires:  - len(attendances_competing) is greater than zero and even
                - len(judges) >= floor(len(attendances) / 2)
                - number of rooms for the day is at least the number of debates

    """
    # Clear any existing debates for the day
    Debate.objects.filter(match_day=match_day).delete()

    attendances_competing = match_day.attendances_competing.all()
    judges = []

    for attendance in match_day.attendances_judging.all():
        for judge in get_qualified_judges(attendance):
            judges.append(judge)

    rooms = list(Room.objects.filter(date=match_day.date))

    # Rank teams
    attendances_competing = rank_attendances(attendances_competing)
    number_of_debates = _number_of_debates(len(attendances_competing))

    debates = []
    # Generate the debate objects
    for i in range(0, number_of_debates):
        attendance1 = attendances_competing.pop(0)
        # Find opponent
        TEAM_WINS_DELTA_LIMIT = 1
        for j, attendance in enumerate(attendances_competing):
            # TODO: can optimise so that we don't go through entire list
            if not is_debated_before(attendance1.team, attendance.team) and \
                    abs(attendance1.team.get_wins() - attendance.team.get_wins()) <= \
                        TEAM_WINS_DELTA_LIMIT:
                attendance2 = attendances_competing.pop(j)
                break
        else:
            # No opponent found that attendance1's team has not VS'ed before
            # In this case just debate with the highest ranked team
            attendance2 = attendances_competing.pop(0)


        debate = Debate()
        debate.match_day = match_day

        assign_aff_neg(debate, attendance1, attendance2)
        debate.save() # For ManyToManyRelation for judges

        # Assign judges - do this circularly (i.e. if there are excess judges
        # assign to higher ranked debates in order)
        judge_indices = range(i, len(judges), number_of_debates)
        for judge_index in judge_indices:
            debate.judges.add(judges[judge_index])
        
        # Assign room
        debate.room = rooms[i]

        debate.save()
        debates.append(debate)

    # Check for vetoes
    # The reason to use another for loop is to make sure that all the debates
    # are generated beforehand, so that if the algorithm can't find a working
    # solution in the end, at least it can give a partially working one
    for i, debate in enumerate(debates):
        affirmative = debate.affirmative
        negative = debate.negative

        vetoes_for_debate = get_vetoes(affirmative, negative) + get_vetoes(negative, affirmative)

        if vetoes_for_debate:
            print("veto: ", affirmative.team.name, negative.team.name)
            # Swap lower ranked team in debate with the highest ranked non-vetoed
            # attendance ranked below
            debates_below = [debates[j] for j in range(i+1, len(debates))]
            lower_ranked_team = rank_attendances([affirmative, negative])[1]
            lower_ranked_team_attr = get_attr_for_attendance(debate, lower_ranked_team)
            swap_details = find_attendance_to_swap(lower_ranked_team, debates_below)
            if swap_details is not None:
                debate_to_swap, attendance_attr = swap_details
                attendance_to_swap = getattr(debate_to_swap, attendance_attr)
                print("swap: ", lower_ranked_team.team.name, attendance_to_swap.team.name)
                # Swap lower_ranked_team with attendace_to_swap
                if lower_ranked_team_attr == "affirmative":
                    debate.affirmative = attendance_to_swap
                elif lower_ranked_team_attr == "negative":
                    debate.negative = attendance_to_swap
                if attendance_attr == "affirmative":
                    debate_to_swap.affirmative = lower_ranked_team
                elif attendance_attr == "negative":
                    debate_to_swap.negative = lower_ranked_team
                # TODO: Add to debates_affected counter for Veto
                for veto in vetoes_for_debate:
                    veto.affected_debates += 1
                    veto.save()
                # Now reassign aff and neg sides for the affected debates
                assign_aff_neg(debate, debate.affirmative, debate.negative).save()
                assign_aff_neg(debate_to_swap, debate_to_swap.affirmative, debate_to_swap.negative).save()
            else:
                # No available attendance to swap with - raise exception for now
                raise CannotFindWorkingConfigurationException(
                    "Cannot allocate debates that satisfy veto criteria - you may wish to change the debates generated."
                )
                # TODO: use a status code instead?

    return match_day

def generate_debates(date, **kwargs):
    """
    Generates debates given the date.
    Instantiates Debate objects and saves them to the database.

    :param attendances: Attendances to generate debates for
    :return: the generated MatchDay
    """
    match_day = _matchmake(assign_teams_for_date(date, **kwargs))
    match_day.save()
    return match_day
