from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .forms import TeamAttendanceForm

context = {
    'speaker_ids': [1, 2, 3]
}

def index(request):
    return render(request, 'attendanceform/index.html', context)

def markattendance(request):
    if request.method == 'POST':
        form = TeamAttendanceForm(request.POST)
        if form.is_valid():
            form.save()

            return HttpResponse("Team attendance marked.")


    form = TeamAttendanceForm()
    return render(request, 'attendanceform/form.html', {'form': form})

def result(request):
    response = "Your attendance has been marked."
    return HttpResponse(response)
