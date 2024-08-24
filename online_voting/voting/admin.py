from django.contrib import admin
from .models import VotingEvent,Candidate,Vote,Category,Profile

admin.site.register(VotingEvent)
admin.site.register(Candidate)
admin.site.register(Vote)
admin.site.register(Category)
admin.site.register(Profile)