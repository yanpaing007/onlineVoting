from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory, ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
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
    # Get base queryset
    events = VotingEvent.objects.all()
    
    # If user is not authenticated, only show non-private events
    if not request.user.is_authenticated:
        events = events.filter(is_private=False)
    
    # Get filter parameters
    status_filter = request.GET.get('status')
    sort_by = request.GET.get('sort', 'latest')
    category_id = request.GET.get('category')
    
    # Apply category filter
    if category_id:
        events = events.filter(categories__id=category_id)
        selected_category = get_object_or_404(Category, id=category_id)
    else:
        selected_category = None
    
    # Get categories for the filter dropdown
    categories = Category.objects.all()
    
    # Convert events to user timezone and add status
    user_timezone = request.user.profile.timezone if request.user.is_authenticated else 'UTC'
    now = timezone.now()
    
    # Apply status filter and annotate status
    if status_filter:
        if status_filter == 'ongoing':
            events = events.filter(start_time__lte=now, end_time__gte=now)
        elif status_filter == 'upcoming':
            events = events.filter(start_time__gt=now)
        elif status_filter == 'ended':
            events = events.filter(end_time__lt=now)
    
    # Apply sorting
    if sort_by == 'latest':
        events = events.order_by('-created_at')
    elif sort_by == 'oldest':
        events = events.order_by('created_at')
    elif sort_by == 'popular':
        events = events.annotate(
            favorite_count=Count('favorited_by'),
            vote_count=Count('votes')
        ).order_by('-favorite_count', '-vote_count', '-created_at')
    elif sort_by == 'upcoming':
        events = events.filter(start_time__gt=now).order_by('start_time')
    
    # Convert to user's timezone and add status
    for event in events:
        formatter = DatetimeFormatter(event, user_timezone)
        event = formatter.set_user_time()
        
        if event.start_time <= now <= event.end_time:
            event.status = 'ongoing'
        elif now < event.start_time:
            event.status = 'upcoming'
        else:
            event.status = 'ended'

    return render(
        request,
        "voting/event_list.html",
        {
            "events": events,
            "categories": categories,
            "selected_category": selected_category,
            "status_filter": status_filter,
            "sort_by": sort_by,
        },
    )


def event_by_category(request, cate):
    category = get_object_or_404(Category, name=cate)
    events = VotingEvent.objects.filter(categories=category)
    
    # Get filter parameters
    status_filter = request.GET.get('status')
    sort_by = request.GET.get('sort', 'latest')
    
    # Filter private events for non-authenticated users
    if not request.user.is_authenticated:
        events = events.filter(is_private=False)
    
    # Get categories for the filter dropdown
    categories = Category.objects.all()
    
    # Convert events to user timezone and add status
    user_timezone = request.user.profile.timezone if request.user.is_authenticated else 'UTC'
    now = timezone.now()
    
    # Apply status filter
    if status_filter:
        if status_filter == 'ongoing':
            events = events.filter(start_time__lte=now, end_time__gte=now)
        elif status_filter == 'upcoming':
            events = events.filter(start_time__gt=now)
        elif status_filter == 'ended':
            events = events.filter(end_time__lt=now)
    
    # Apply sorting
    if sort_by == 'latest':
        events = events.order_by('-created_at')
    elif sort_by == 'oldest':
        events = events.order_by('created_at')
    elif sort_by == 'popular':
        events = events.annotate(
            favorite_count=Count('favorited_by'),
            vote_count=Count('votes')
        ).order_by('-favorite_count', '-vote_count', '-created_at')
    elif sort_by == 'upcoming':
        events = events.filter(start_time__gt=now).order_by('start_time')
    
    # Convert to user's timezone and add status
    for event in events:
        formatter = DatetimeFormatter(event, user_timezone)
        event = formatter.set_user_time()
        
        if event.start_time <= now <= event.end_time:
            event.status = 'ongoing'
        elif now < event.start_time:
            event.status = 'upcoming'
        else:
            event.status = 'ended'

    return render(
        request,
        "voting/event_list.html",
        {
            "events": events,
            "categories": categories,
            "selected_category": category,
            "status_filter": status_filter,
            "sort_by": sort_by,
        },
    )


def search_events(request):
    query = request.GET.get('q')
    events = VotingEvent.objects.all()
    
    # Get filter parameters
    status_filter = request.GET.get('status')
    sort_by = request.GET.get('sort', 'latest')
    category_id = request.GET.get('category')
    
    # Filter private events for non-authenticated users
    if not request.user.is_authenticated:
        events = events.filter(is_private=False)
    
    # Apply search filter
    if query:
        events = events.filter(event_name__icontains=query)
    
    # Apply category filter
    if category_id:
        events = events.filter(categories__id=category_id)
        selected_category = get_object_or_404(Category, id=category_id)
    else:
        selected_category = None
    
    # Get categories for the filter dropdown
    categories = Category.objects.all()
    
    # Convert events to user timezone and add status
    user_timezone = request.user.profile.timezone if request.user.is_authenticated else 'UTC'
    now = timezone.now()
    
    # Apply status filter
    if status_filter:
        if status_filter == 'ongoing':
            events = events.filter(start_time__lte=now, end_time__gte=now)
        elif status_filter == 'upcoming':
            events = events.filter(start_time__gt=now)
        elif status_filter == 'ended':
            events = events.filter(end_time__lt=now)
    
    # Apply sorting
    if sort_by == 'latest':
        events = events.order_by('-created_at')
    elif sort_by == 'oldest':
        events = events.order_by('created_at')
    elif sort_by == 'popular':
        events = events.annotate(
            favorite_count=Count('favorited_by'),
            vote_count=Count('votes')
        ).order_by('-favorite_count', '-vote_count', '-created_at')
    elif sort_by == 'upcoming':
        events = events.filter(start_time__gt=now).order_by('start_time')
    
    # Convert to user's timezone and add status
    for event in events:
        formatter = DatetimeFormatter(event, user_timezone)
        event = formatter.set_user_time()
        
        if event.start_time <= now <= event.end_time:
            event.status = 'ongoing'
        elif now < event.start_time:
            event.status = 'upcoming'
        else:
            event.status = 'ended'
    
    return render(
        request,
        "voting/event_list.html",
        {
            "events": events,
            "categories": categories,
            "selected_category": selected_category,
            "status_filter": status_filter,
            "sort_by": sort_by,
            "search_query": query,
        },
    )


def delete_event(request, event_id):
    event = get_object_or_404(VotingEvent, id=event_id)
    event.delete()
    return redirect('voting:my_events')


def category_list(request):
    categories = Category.objects.all()
    category_colors = {
        'Music': '#ff5733',
        'Travel': '#33ff57',
        'Automobile': '#3357ff',
        'Mobile': 'blue',
        'Animations': 'cyan',
        'Movies': 'maroon',
        'Entertainment': 'red',
        'Food and drinks': 'lightgreen'
    }
    for category in categories:
        category.color = category_colors.get(category.name, '#6c757d')
        
    return render(request, "voting/category_list.html", {
        "categories": categories,
    })


def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    events = VotingEvent.objects.filter(categories=category)
    
    # Get filter parameters
    status_filter = request.GET.get('status')
    sort_by = request.GET.get('sort', 'latest')
    
    # Filter private events for non-authenticated users
    if not request.user.is_authenticated:
        events = events.filter(is_private=False)
    
    # Get categories for the filter dropdown
    categories = Category.objects.all()
    
    # Convert events to user timezone and add status
    user_timezone = request.user.profile.timezone if request.user.is_authenticated else 'UTC'
    now = timezone.now()
    
    # Apply status filter
    if status_filter:
        if status_filter == 'ongoing':
            events = events.filter(start_time__lte=now, end_time__gte=now)
        elif status_filter == 'upcoming':
            events = events.filter(start_time__gt=now)
        elif status_filter == 'ended':
            events = events.filter(end_time__lt=now)
    
    # Apply sorting
    if sort_by == 'latest':
        events = events.order_by('-created_at')
    elif sort_by == 'oldest':
        events = events.order_by('created_at')
    elif sort_by == 'popular':
        events = events.annotate(
            favorite_count=Count('favorited_by'),
            vote_count=Count('votes')
        ).order_by('-favorite_count', '-vote_count', '-created_at')
    elif sort_by == 'upcoming':
        events = events.filter(start_time__gt=now).order_by('start_time')
    
    # Convert to user's timezone and add status
    for event in events:
        formatter = DatetimeFormatter(event, user_timezone)
        event = formatter.set_user_time()
        
        if event.start_time <= now <= event.end_time:
            event.status = 'ongoing'
        elif now < event.start_time:
            event.status = 'upcoming'
        else:
            event.status = 'ended'

    return render(
        request,
        "voting/event_list.html",
        {
            "events": events,
            "categories": categories,
            "selected_category": category,
            "status_filter": status_filter,
            "sort_by": sort_by,
        },
    )


@login_required
def delete_category(request, category_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete categories.")
        return redirect('voting:category_list')
    
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, f"Category '{category.name}' has been deleted.")
    return redirect('voting:category_list')


def landing_page(request):
    """Landing page view that showcases the main features of the voting system"""
    return render(request, "voting/landing_page.html")
