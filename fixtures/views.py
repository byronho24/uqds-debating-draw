from django.shortcuts import render
from django.http import HttpResponse
from datetime import date, datetime
from . import allocator
from .models import Attendance, Speaker, Team, Score, Match

def fixtures(request):

    # Check whether fixtures are already generated
    matches = Match.objects.filter(date=date.today())

    if matches:
        debates = []
        for match in matches:
            attendances = match.attendances.all()
            debates.append({
                'match_id': match.id,
                'attendance1': attendances[0],
                'attendance2': attendances[1],
                'judge': match.judge
            })

    else:
        # Generate fixtures
        # Retrieve all the attendance data for the day
        attendances = list(Attendance.objects.filter(timestamp__date=date.today()))
        competing_attendances, judges = allocator.assign_competing_teams(attendances)
        debates = allocator.matchmake(competing_attendances, judges)

        for debate in debates:
            # Save generated fixtures to database
            match = Match()
            match.date = date.today()
            match.judge = debate['judge']
            match.save()
            match.attendances.add(debate['attendance1'], debate['attendance2'])
            match.save()

            # Add match_id to entries in debates
            debate['match_id'] = match.id

    return render(request, 'fixtures/fixtures.html', {'debates': debates})

def detail(request, match_id: int):
    return HttpResponse(f"You are looking at match {match_id}.")
