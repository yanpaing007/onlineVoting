import pytz
from zoneinfo import ZoneInfo
from django.utils import timezone

class DatetimeFormatter:
    def __init__(self, event, user_timezone='UTC'):        
        self.event = event
        self.user_timezone = ZoneInfo(user_timezone) if 'ZoneInfo' in globals() else pytz.timezone(user_timezone)

    def set_user_time(self):
        self.event.start_time = self.event.start_time.replace(tzinfo=self.user_timezone)
        self.event.end_time = self.event.end_time.replace(tzinfo=self.user_timezone)
        return self.event

    def get_user_time(self):
        self.event.start_time = self.event.start_time.astimezone(self.user_timezone)
        self.event.end_time = self.event.end_time.astimezone(self.user_timezone)
        return self.event

    def get_system_time(self):
        self.event.start_time = self.event.start_time.astimezone(pytz.UTC)
        self.event.end_time = self.event.end_time.astimezone(pytz.UTC)
        return self.event

def events_in_user_time(events, user_timezone):
    return [DatetimeFormatter(event, user_timezone).get_user_time() for event in events]

def get_event_status(event, now):
    if event.start_time <= now <= event.end_time:
        return 'ongoing'
    elif event.start_time > now:
        return 'upcoming'
    return 'ended'

def generate_unique_token():
    from django.utils.crypto import get_random_string
    while True:
        token = get_random_string(10)
        from ..models import VotingEvent
        if not VotingEvent.objects.filter(event_token=token).exists():
            return token