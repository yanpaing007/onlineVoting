# voting/models.py

import pytz
from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class VotingEvent(models.Model):
    event_name = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event_token = models.CharField(max_length=10, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    candidate_numbers = models.IntegerField(default=2)
    is_private = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_name


class Candidate(models.Model):
    voting_event = models.ForeignKey(VotingEvent, related_name='candidates', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True) # Description is better since candidates can be anything.
    profile_pic = models.ImageField(upload_to='candidate_pics/', blank=True, null=True)

    def __str__(self):
        return self.name


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
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    timezone = models.CharField(
        max_length=63,
        choices=[(tz, tz) for tz in pytz.all_timezones],
        default='UTC'
    )

    def __str__(self):
        return self.user.username
    
    
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} favorited {self.event.event_name}"
