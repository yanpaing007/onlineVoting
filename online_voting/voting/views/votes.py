from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from ..models import Vote, VotingEvent, Candidate
from .utils import get_event_status, timezone

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


def vote_result(request, event_id):
    voting_event = get_object_or_404(VotingEvent, id=event_id)
    candidates = voting_event.candidates.all()
    return render(
        request,
        "voting/vote_result.html",
        {"event": voting_event, "candidates": candidates, "status": get_event_status(voting_event, timezone.now())},
    )