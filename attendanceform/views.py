from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

context = {
    'speaker_ids': [1, 2, 3]
}

def index(request):
    return render(request, 'attendanceform/index.html', context)

def markattendance(request):
    return HttpResponseRedirect(reverse("attendanceform:result"))

def result(request):
    response = "Your attendance has been marked."
    return HttpResponse(response)
