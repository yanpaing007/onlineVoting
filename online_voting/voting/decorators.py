from django.contrib.auth.decorators import user_passes_test
from .models import VotingEvent
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden

def event_owner_required(view_func):
    def wrapper(request, *args, **kwargs):
        event = get_object_or_404(VotingEvent, pk=kwargs['event_id'])
        if request.user != event.created_by:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return wrapper