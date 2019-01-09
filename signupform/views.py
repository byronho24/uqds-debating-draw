from django.shortcuts import render
from django.http import HttpResponse

def index(request):
        context = {
            'speaker_ids': [1, 2, 3, 4, 5],
        }
    return render(request, 'signupform/index.html', context)
