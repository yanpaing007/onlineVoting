# voting/urls.py

from django.urls import path

from voting.views import *

app_name = 'voting'

urlpatterns = [
    path('', event_list, name='event_list'),  # List all voting events
    path('event/<int:event_id>/', event_detail, name='event_detail_by_id'),
    path('event/token/<str:event_token>/', event_detail, name='event_detail_by_token'),
    path('event/create', create_event, name='create_event'),  # Create a new voting event
    path('event/<int:event_id>/vote', vote, name='vote'),  # Vote on a specific event
    path('event/<int:event_id>/results', vote_result, name='vote_result'),  # View results for a specific event
    path('event/myevents', my_events, name='my_events'),
    path('event/<str:cate>', event_by_category, name='sort_by_category'),
    path('profile/', profile, name='profile'),
    path('event/search/', search_events, name="search_events"),
    path('event/delete/<int:event_id>/', delete_event, name='delete_event'),
    path('event/<int:event_id>/status/', get_event_status, name='event_status'),
]
