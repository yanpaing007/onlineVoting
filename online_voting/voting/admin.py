from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Category, VotingEvent, Candidate, Vote, Profile, Favorite

class VoteInline(admin.TabularInline):
    model = Vote
    extra = 0  # No extra empty forms
    fields = ('voter', 'candidate', 'is_anonymous')
    readonly_fields = ('voter', 'candidate', 'is_anonymous')

    def has_add_permission(self, request, obj=None):
        # Prevent adding votes directly through this inline in VotingEvent
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'view_events_link')
    search_fields = ('name',)
    ordering = ('name',)

    def view_events_link(self, obj):
        """Generates a link to view VotingEvents associated with this Category"""
        url = reverse('admin:voting_votingevent_changelist') + f'?categories__id__exact={obj.id}'
        return format_html(f'<a href="{url}">View Events</a>')

    view_events_link.short_description = "Events"


@admin.register(VotingEvent)
class VotingEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_name', 'start_time', 'end_time', 'created_by', 'is_private', 'created_at', 'view_voters_link')
    search_fields = ('event_name', 'created_by__username')
    list_filter = ('is_private', 'categories')
    ordering = ('-created_at',)
    filter_horizontal = ('categories',)
    date_hierarchy = 'start_time'
    inlines = [VoteInline]  # Inline display of voters

    def view_voters_link(self, obj):
        """Generates a link to view voters for this VotingEvent"""
        url = reverse('admin:voting_vote_changelist') + f'?voting_event__id__exact={obj.id}'
        return format_html(f'<a href="{url}">View Voters</a>')

    view_voters_link.short_description = "Voters"


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'voting_event', 'description')
    search_fields = ('name', 'voting_event__event_name')
    list_filter = ('voting_event',)
    ordering = ('voting_event', 'name')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'voting_event', 'candidate', 'voter', 'is_anonymous')
    search_fields = ('voting_event__event_name', 'candidate__name', 'voter__username')
    list_filter = ('voting_event', 'is_anonymous')
    ordering = ('voting_event',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'birthday', 'timezone')
    search_fields = ('user__username', 'timezone')
    ordering = ('user',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'added_at')
    search_fields = ('user__username', 'event__event_name')
    list_filter = ('user', 'event')
    ordering = ('-added_at',)
