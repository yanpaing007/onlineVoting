from django.db import models
from .voting_event import VotingEvent
from .candidate import Candidate
from django.contrib.auth.models import User

class Vote(models.Model):
    voting_event = models.ForeignKey(VotingEvent, related_name='votes', on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, related_name='votes', on_delete=models.CASCADE)
    voter = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        unique_together = ('voting_event', 'voter')

    def __str__(self):
        voter_name = (
            self.voter.username if self.voter and not self.is_anonymous else 'Anonymous'
        )
        return f"{self.candidate.name} - {voter_name}"