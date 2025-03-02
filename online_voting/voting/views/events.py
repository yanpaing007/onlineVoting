from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from zoneinfo import ZoneInfo
from django.http import Http404
from datetime import timedelta
import pytz

from ..models import VotingEvent, Candidate, Category, Favorite, Vote
from ..forms import VotingEventForm, CandidateForm
from .utils import DateTimeFormatter, get_event_status, generate_unique_token, events_in_user_time


@login_required
def create_event(request):
    CandidateFormSet = modelformset_factory(Candidate, form=CandidateForm, extra=0)
    
    if request.method == "POST":
        event_form = VotingEventForm(request.POST)
        candidate_formset = CandidateFormSet(request.POST, request.FILES)
        
        if event_form.is_valid() and candidate_formset.is_valid():
            if candidate_formset.total_form_count() < 2:
                messages.error(request, "* You must add at least 2 candidates.")
            else:
                try:
                    # Create and save voting event with form data
                    voting_event = event_form.save(commit=False)
                    voting_event.created_by = request.user
                    
                    # Handle timezone conversions
                    user_timezone = request.user.profile.timezone
                    formatter = DateTimeFormatter(voting_event, user_timezone)
                    voting_event = formatter.to_system_timezone()
                    
                    # Generate token for private events
                    if voting_event.is_private:
                        voting_event.event_token = generate_unique_token()
                    
                    # Save to database FIRST to get ID
                    voting_event.save()
                    
                    # Save many-to-many relationships (categories)
                    event_form.save_m2m()  # This handles categories automatically

                    # Save candidates
                    for form in candidate_formset:
                        if form.is_valid() and form.cleaned_data.get('name'):
                            candidate = form.save(commit=False)
                            candidate.voting_event = voting_event
                            candidate.save()

                    return redirect("voting:event_detail_by_id", event_id=voting_event.id)
                
                except RuntimeError as e:
                    messages.error(request, str(e))
        
        return render(request, "voting/create_event.html", {
            "event_form": event_form,
            "candidate_formset": candidate_formset,
        })


def event_detail(request, event_id=None, event_token=None):
    voting_event = _get_event_or_404(event_id, event_token)
    user_timezone = _get_user_timezone(request.user)
    
    # Convert event times to user's local timezone
    formatter = DateTimeFormatter(voting_event, user_timezone)
    local_event = formatter.to_user_timezone()
    
    context = _build_event_context(request, local_event, user_timezone)
    
    if request.method == "POST" and 'favorite' in request.POST:
        return _handle_favorite_toggle(request, voting_event)
    
    return render(request, "voting/event_detail.html", context)

# Helper functions
def _get_event_or_404(event_id, event_token):
    """Retrieve event by ID or token"""
    if event_id:
        return get_object_or_404(VotingEvent, id=event_id)
    if event_token:
        return get_object_or_404(VotingEvent, event_token=event_token)
    raise Http404("No event specified")

def _get_user_timezone(user):
    """Get user's timezone with fallback to UTC"""
    if user.is_authenticated and hasattr(user, 'profile'):
        return user.profile.timezone
    return 'UTC'

def _build_event_context(request, event, user_timezone):
    """Construct context with localized datetime"""
    now = timezone.localtime(timezone.now(), timezone=_get_tz_object(user_timezone))
    
    status, total_seconds = _calculate_event_status_and_time(event, now)
    
    return {
        "event": event,
        "candidates": event.candidates.all(),
        "voted_candidate": _get_user_vote(request.user, event),
        "status": status,
        "total_seconds": total_seconds,
        'is_favorited': _is_event_favorited(request.user, event),
    }

def _get_tz_object(timezone_str):
    """Get timezone object from string"""
    return ZoneInfo(timezone_str) if ZoneInfo else pytz.timezone(timezone_str)

def _calculate_event_status_and_time(event, reference_time):
    """Calculate status and remaining time based on localized datetimes"""
    status = get_event_status(event, reference_time)
    
    if status == 'upcoming':
        delta = event.start_time - reference_time
    elif status == 'ongoing':
        delta = event.end_time - reference_time
    else:
        delta = timedelta(0)
    
    return status, int(delta.total_seconds())

def _get_user_vote(user, event):
    """Get user's vote candidate if exists"""
    if not user.is_authenticated:
        return None
    vote = Vote.objects.filter(voting_event=event, voter=user).first()
    return vote.candidate if vote else None

def _is_event_favorited(user, event):
    """Check if event is favorited by user"""
    return user.is_authenticated and Favorite.objects.filter(
        user=user, event=event
    ).exists()

def _handle_favorite_toggle(request, event):
    """Toggle favorite status and redirect"""
    if _is_event_favorited(request.user, event):
        Favorite.objects.filter(user=request.user, event=event).delete()
    else:
        Favorite.objects.create(user=request.user, event=event)
    return redirect('voting:event_detail_by_id', event_id=event.id)


def event_list(request):
    now = timezone.localtime()
    categories = Category.objects.all()
    category_colors = {
        'Music': '#ff5733',  # Example color
        'Travel': '#33ff57',
        'Automobile': '#3357ff',
        'Mobile': 'blue',
        'Animations': 'cyan',
        'Movies': 'maroon',
        'Entertainment': 'red',
        'Food and drinks': 'lightgreen'
        # Add more categories and their respective colors here
    }
    for category in categories:
        category.color = category_colors.get(category.name, '#6c757d')  # Default color if not found
    all_events = VotingEvent.objects.filter(is_private=False)

    ongoing = all_events.filter(start_time__lte=now, end_time__gte=now)
    upcoming = all_events.filter(start_time__gt=now)
    previous = all_events.filter(end_time__lt=now)

    user_timezone = request.user.profile.timezone if request.user.is_authenticated else 'UTC'

    context = {
        "ongoing_events": events_in_user_time(ongoing, user_timezone),
        "upcoming_events": events_in_user_time(upcoming, user_timezone),
        "previous_events": events_in_user_time(previous, user_timezone),
        # ... rest of context ...
    }

    return render(request, "voting/home.html", context)


def event_by_category(request, cate):
    category = get_object_or_404(Category, name=cate)
    events = VotingEvent.objects.filter(categories=category)

    return render(
        request,
        "voting/event_list.html",
        {"events": events, "selected_category": category},
    )


def search_events(request):
    all_events = VotingEvent.objects.filter(is_private=False)
    query = request.GET.get('query')
    results = []
    
    if query and len(query) >= 3:
        results = all_events.filter(event_name__icontains=query)
    else:
        messages.error(request, "Invalid input")
        
    return render(request, 'voting/search_results.html', {'results': results, 'query': query})


def delete_event(request, event_id):
    event = get_object_or_404(VotingEvent, id=event_id)
    event.delete()
    return redirect('voting:my_events')
