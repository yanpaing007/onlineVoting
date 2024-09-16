# voting/urls.py

from django.urls import path
from . import views

app_name = 'voting'

urlpatterns = [
    path('', views.event_list, name='event_list'),  # List all voting events
    path('event/<int:event_id>/', views.event_detail, name='event_detail_by_id'),
    path('event/token/<str:event_token>/', views.event_detail, name='event_detail_by_token'),
    path('event/create', views.create_event, name='create_event'),  # Create a new voting event
    path('event/<int:event_id>/vote', views.vote, name='vote'),  # Vote on a specific event
    path('event/<int:event_id>/results', views.vote_result, name='vote_result'),  # View results for a specific event
    path('event/myevents', views.my_events, name='my_events'),
    path('event/<str:cate>', views.event_by_category, name='sort_by_category'),
    path('profile/', views.profile, name='profile'),
    path('event/search/', views.search_events, name="search_events"),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    path('event/<int:event_id>/status/', views.get_event_status, name='event_status'),
]
