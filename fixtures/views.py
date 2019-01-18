from django.shortcuts import render
from django.http import HttpResponse
from datetime import date, datetime
from . import allocator
from .models import Attendance, Speaker, Team, Score, Match

def fixtures(request):

    # Check whether fixtures are already generated
    matches = Match.objects.filter(date=date.today())
    if matches:
        # Matches already assigned
        debates = []
        for match in matches:
            debate = []
            for attendance in match.attendances.all():
                debate.append(attendance)
            debate.append(match.judge)
            debates.append(debate)

    else:
        # Generate fixtures
        # Retrieve all the attendance data for the day
        attendances = list(Attendance.objects.filter(timestamp__date=date.today()))
        competing_attendances, judges = allocator.assign_competing_teams(attendances)
        debates = allocator.matchmake(competing_attendances, judges)

        # Save generated fixtures to database
        for debate in debates:
            match = Match()
            match.date = date.today()
            match.judge = debate[2]
            match.save()
            match.attendances.add(debate[0], debate[1])
            match.save()

    return render(request, 'fixtures/fixtures.html', {'debates': debates})
