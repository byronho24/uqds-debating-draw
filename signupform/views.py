from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

context = {
    'speaker_ids': [1, 2, 3, 4, 5]
}

def index(request):
    return render(request, 'signupform/index.html', context)

def signup(request):
    result = ""
    for i in context['speaker_ids']:
        speaker_name = request.POST["speaker_" + str(i)]
        result += speaker_name + "\n"
    return HttpResponse(result) #TODO: Redirect
