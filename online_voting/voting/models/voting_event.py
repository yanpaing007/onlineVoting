from django.db import models
from django.contrib.auth.models import User
from .category import Category

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