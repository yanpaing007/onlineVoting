from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from ..models import Profile, VotingEvent, Favorite
from ..forms import UserUpdateForm, ProfileUpdateForm


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

@login_required
def my_events(request):
    events = VotingEvent.objects.filter(created_by=request.user)
    voted_events = VotingEvent.objects.filter(votes__voter=request.user).distinct()
    favorites = Favorite.objects.filter(user=request.user).select_related('event')
    return render(request, "voting/myevent.html", {"events": events, "voted_events": voted_events, "favorites": favorites})
