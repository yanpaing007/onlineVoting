from django.db import models
from .voting_event import VotingEvent

class Candidate(models.Model):
    voting_event = models.ForeignKey(VotingEvent, related_name='candidates', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='candidate_pics/', blank=True, null=True)

    def __str__(self):
        return self.name