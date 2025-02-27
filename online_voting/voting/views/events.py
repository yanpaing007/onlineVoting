from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from ..models import VotingEvent, Candidate, Category, Favorite, Vote
from ..forms import VotingEventForm, CandidateForm
from .utils import DatetimeFormatter, get_event_status, generate_unique_token, events_in_user_time
from django.utils import timezone

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

    status = get_event_status(voting_event, now)
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


def event_list(request):
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

    ongoing = all_events.filter(start_time__lte=now, end_time__gte=now)
    upcoming = all_events.filter(start_time__gt=now)
    previous = all_events.filter(end_time__lt=now)

    context = {
        "ongoing_events": ongoing,
        "upcoming_events": upcoming,
        "previous_events": previous,
        "categories": categories,
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
