import random
import time
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import ValidationError, modelformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views import View
from .models import VotingEvent, Candidate, Vote, Category, Profile , Favorite
import pytz
from zoneinfo import ZoneInfo

# voting/views.py

from .forms import (
    ProfileUpdateForm,
    UserUpdateForm,
    VotingEventForm,
    CandidateForm,
    RegisterForm,
)

# To resolve Timezone differences.
class DatetimeFormatter:
    def __init__(self, event, user_timezone='UTC'):        
        self.event = event
        self.user_timezone = ZoneInfo(user_timezone) if 'ZoneInfo' in globals() else pytz.timezone(user_timezone)

    # Format Input Datetime to user local timezone
    def set_user_time(self):
        self.event.start_time = self.event.start_time.replace(tzinfo=self.user_timezone)
        self.event.end_time = self.event.end_time.replace(tzinfo=self.user_timezone)
        return self.event

    # Convert System time to user local time.
    def get_user_time(self):
        self.event.start_time = self.event.start_time.astimezone(self.user_timezone)
        self.event.end_time = self.event.end_time.astimezone(self.user_timezone)
        return self.event

    # Convert user local time to system time (UTC). 
    def get_system_time(self):
        self.event.start_time = self.event.start_time.astimezone(pytz.UTC)
        self.event.end_time = self.event.end_time.astimezone(pytz.UTC)
        return self.event

def events_in_user_time(events, user_timezone):
    result = []
    for event in events:
        formatter = DatetimeFormatter(event, user_timezone)
        event = formatter.get_user_time()
        result.append(event)
    return result

#Return current status of Event.
def event_status(event, now):
    ongoing = event.start_time <= now and event.end_time >= now
    upcoming = event.start_time > now
    previous = event.end_time < now
    if ongoing:
        return 'ongoing'
    elif upcoming:
        return 'upcoming'
    elif previous:
        return 'ended'
    
    return None




def get_event_status(request, event_id):
    voting_event = get_object_or_404(VotingEvent, id=event_id)
    now = timezone.now()
    
    status = event_status(voting_event, now)
    if status == 'upcoming':
        time_remaining = voting_event.start_time - now
        total_seconds = int(time_remaining.total_seconds())
    elif status == 'ongoing':
        time_remaining = voting_event.end_time - now
        total_seconds = int(time_remaining.total_seconds())
    else:
        total_seconds = 0

    return JsonResponse({
        'status': status,
        'total_seconds': total_seconds,
    })

# Generate a unique token for private events
def generate_unique_token():
    while True:
        token = get_random_string(10)
        if not VotingEvent.objects.filter(event_token=token).exists():
            return token
        


# Create a new voting event
@login_required
def create_event(request):
    CandidateFormSet = modelformset_factory(Candidate, form=CandidateForm, extra=0)
    
    if request.method == "POST":
        event_form = VotingEventForm(request.POST)
       
        candidate_formset = CandidateFormSet(request.POST, request.FILES)
        print(event_form.is_valid())
        
        if event_form.is_valid() and candidate_formset.is_valid():
            # Ensure at least two candidates are provided
            if candidate_formset.total_form_count() < 2:
                candidate_formset._non_form_errors.append(
                    ValidationError("* You must add at least 2 candidates.")
                )
            else:
                # Proceed with saving the event
                voting_event = event_form.save(commit=False)
                voting_event.created_by = request.user

                # Get User Input Datetime and Timezone
                voting_event.start_time = event_form.cleaned_data['start_time']
                voting_event.end_time = event_form.cleaned_data['end_time']
                user_timezone = request.user.profile.timezone

                # Format Datetime to user local time
                formatter = DatetimeFormatter(voting_event, user_timezone)
                voting_event = formatter.set_user_time()

                # Convert user local time to system time (UTC)
                formatter = DatetimeFormatter(voting_event)
                voting_event = formatter.get_system_time()

                if voting_event.is_private:
                    voting_event.event_token = generate_unique_token()

                # Save the voting event
                voting_event.save()

                # Assign categories to the voting event
                selected_categories = event_form.cleaned_data["categories"]
                voting_event.categories.set(selected_categories)

                # Save each candidate related to the voting event
                for form in candidate_formset:
                    if form.is_valid() and form.cleaned_data.get('name'):
                      candidate = form.save(commit=False)
                      candidate.voting_event = voting_event
                      candidate.save()

                # Redirect to event detail page
                return redirect("voting:event_detail_by_id", event_id=voting_event.id)
        if candidate_formset.total_form_count() < 2:
            messages.error(request, "* You must add at least 2 candidates.")
        else:
            messages.error(request, "Please correct the errors below.")
            
            
    else:
        event_form = VotingEventForm()
        candidate_formset = CandidateFormSet(queryset=Candidate.objects.none())

    return render(
        request,
        "voting/create_event.html",
        {
            "event_form": event_form,
            "candidate_formset": candidate_formset,
        },
    )


# View event details
@login_required
def event_detail(request, event_id=None, event_token=None):
    now = timezone.now()
    total_seconds = 0

    if event_id:
        # Fetch VotingEvent by event_id
        voting_event = get_object_or_404(VotingEvent, id=event_id)

    elif event_token != None:
        # Fetch VotingEvent by event_token
        voting_event = get_object_or_404(VotingEvent, event_token=event_token)
      
    is_favorited = Favorite.objects.filter(user=request.user, event=voting_event).exists()

    if request.method == "POST" and 'favorite' in request.POST:
        if is_favorited:
            Favorite.objects.filter(user=request.user, event=voting_event).delete()
        else:
            Favorite.objects.create(user=request.user, event=voting_event)
        return redirect('voting:event_detail_by_id', event_id=voting_event.id)

      
    candidates = voting_event.candidates.all()
    user_vote = Vote.objects.filter(voting_event=voting_event, voter=request.user).first()
    voted_candidate = user_vote.candidate if user_vote else None

    status = event_status(voting_event, now)
    if status == 'upcoming':
        time_remaining = voting_event.start_time - now
        total_seconds = int(time_remaining.total_seconds())
    elif status == 'ongoing':
        time_remaining = voting_event.end_time - now
        total_seconds = int(time_remaining.total_seconds())

    context = {
        "event": voting_event,
        "candidates": candidates,
        "voted_candidate": voted_candidate,
        "status": status,  # Ensure this is a string value
        "total_seconds": total_seconds,
        'is_favorited': is_favorited,
    }
    return render(request, "voting/event_detail.html", context)

# Vote on an event
@login_required
def vote(request, event_id):
    event = get_object_or_404(VotingEvent, pk=event_id)

    # Check if the user has already voted for this event
    if Vote.objects.filter(voting_event=event, voter=request.user).exists():
        messages.error(request, "You have already voted for this event!")
        return redirect("voting:event_detail_by_id", event_id=event.id)

    if request.method == "POST":
        candidate_id = request.POST.get("candidate")
        anonymous_vote = request.POST.get("anonymousVote")

        if not candidate_id:
            messages.error(request, "You must select a candidate to vote!")
            return redirect("voting:event_detail_by_id", event_id=event.id)

        candidate = get_object_or_404(Candidate, pk=candidate_id)
        # Save the vote with the voter information
        vote = Vote(candidate=candidate, voting_event=event, voter=request.user)
        if anonymous_vote == "on":
            vote.is_anonymous = True
        vote.save()
        messages.success(request, "Your vote has been cast successfully!")
        return redirect("voting:vote_result", event_id=event.id)

    return redirect("voting:event_detail_by_id", event_id=event.id)


# View voting results
def vote_result(request, event_id):
    voting_event = get_object_or_404(VotingEvent, id=event_id)
    candidates = voting_event.candidates.all()
    return render(
        request,
        "voting/vote_result.html",
        {"event": voting_event, "candidates": candidates, "status": event_status(voting_event, timezone.now())},
    )


# See events by filtering them
@login_required
def event_list(request):
    user_timezone = request.user.profile.timezone
    now = timezone.now()
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

    ongoing_events = all_events.filter(start_time__lte=now, end_time__gte=now)
    upcoming_events = all_events.filter(start_time__gt=now)
    previous_events = all_events.filter(end_time__lt=now)

    #Display in user time
    ongoing = events_in_user_time(ongoing_events, user_timezone)
    upcoming = events_in_user_time(upcoming_events, user_timezone)
    previous = events_in_user_time(previous_events, user_timezone)

    context = {
        "ongoing_events": ongoing,
        "upcoming_events": upcoming,
        "previous_events": previous,
        "categories": categories,
    }

    return render(request, "voting/home.html", context)


# Events created by user
@login_required
def my_events(request):
    user_timezone = request.user.profile.timezone
    events = VotingEvent.objects.filter(created_by=request.user)
    voted_events = VotingEvent.objects.filter(votes__voter=request.user).distinct()
    favorites = Favorite.objects.filter(user=request.user).select_related('event')
    return render(request, "voting/myevent.html", {"events": events, "voted_events": voted_events, "favorites": favorites})


# Update profile
@login_required
def profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)
        profile.save()

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("voting:profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(
        request,
        "voting/profile.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


# Registration view
class RegistrationView(View):
    form_class = RegisterForm
    template_name = "voting/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("voting:event_list")  # Redirect authenticated users
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration Successful!")
            return redirect("login")  # Redirect to login after successful registration
        return render(request, self.template_name, {"form": form})


# Login view
class LoginView(View):
    template_name = "voting/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("voting:event_list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember = request.POST.get("remember")  # Get the value of 'remember' checkbox

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Set session expiration based on 'remember' checkbox
            if remember:
                request.session.set_expiry(1209600)  # Set session to 2 weeks
            else:
                request.session.set_expiry(0)  # Set session to expire at browser close
            messages.success(request, "Login Success!")
            return redirect(
                "voting:event_list"
            )  # Redirect to a success page or home page
        else:
            messages.error(request, "Invalid username or password")

        return render(request, self.template_name)

# Filter by category
def event_by_category(request, cate):
    user_timezone = request.user.profile.timezone
    category = get_object_or_404(Category, name=cate)
    events = VotingEvent.objects.filter(categories=category)

    return render(
        request,
        "voting/event_list.html",
        {"events": events, "selected_category": category},
    )

def search_events(request):
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

