from django.db import models
from django.contrib.auth.models import User
from .voting_event import VotingEvent

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} favorited {self.event.event_name}"