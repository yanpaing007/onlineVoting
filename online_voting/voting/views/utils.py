import pytz
from zoneinfo import ZoneInfo
from django.utils import timezone
from django.utils.crypto import get_random_string
from typing import Iterable, Literal, Optional
from functools import lru_cache
from ..models import VotingEvent


class DateTimeFormatter:
    """Handles timezone-aware datetime conversions for events."""
    
    def __init__(self, event: VotingEvent, user_timezone: str = 'UTC'):
        self.event = event
        self.user_timezone = self._get_timezone(user_timezone)
        self.system_timezone = ZoneInfo('UTC') if ZoneInfo else pytz.UTC

    @staticmethod
    @lru_cache(maxsize=32)
    def _get_timezone(zone_name: str) -> ZoneInfo | pytz.BaseTzInfo:
        """Cached timezone resolution with fallback support."""
        try:
            return ZoneInfo(zone_name) if ZoneInfo else pytz.timezone(zone_name)
        except (pytz.UnknownTimeZoneError, ValueError):
            return ZoneInfo('UTC') if ZoneInfo else pytz.UTC

    def to_user_timezone(self) -> VotingEvent:
        """Returns a new event instance with converted datetimes."""
        return self._convert_timezones(self.user_timezone)

    def to_system_timezone(self) -> VotingEvent:
        """Returns a new event instance with UTC datetimes."""
        return self._convert_timezones(self.system_timezone)

    def _convert_timezones(self, target_tz: ZoneInfo | pytz.BaseTzInfo) -> VotingEvent:
        """Clone event with timezone-aware datetimes."""
        event_copy = VotingEvent(
            start_time=self._convert_datetime(self.event.start_time, target_tz),
            end_time=self._convert_datetime(self.event.end_time, target_tz),
            **{f.name: getattr(self.event, f.name) for f in self.event._meta.fields
               if f.name not in ['start_time', 'end_time']}
        )
        return event_copy

    @staticmethod
    def _convert_datetime(dt: timezone.datetime, target_tz) -> timezone.datetime:
        """Safe datetime conversion with zone awareness checks."""
        if not timezone.is_aware(dt):
            dt = timezone.make_aware(dt, timezone=timezone.utc)
        return dt.astimezone(target_tz)


def events_in_user_time(
    events: Iterable[VotingEvent], 
    user_timezone: str
) -> list[VotingEvent]:
    """Batch convert events to user's timezone."""
    return [DateTimeFormatter(event, user_timezone).to_user_timezone()
            for event in events]


def get_event_status(
    event: VotingEvent, 
    reference_time: Optional[timezone.datetime] = None
) -> Literal['ongoing', 'upcoming', 'ended']:
    """Determine event status with timezone-aware comparison."""
    now = reference_time or timezone.now()
    
    if not timezone.is_aware(now):
        now = timezone.make_aware(now, timezone=timezone.utc)
    
    if event.start_time <= now <= event.end_time:
        return 'ongoing'
    return 'upcoming' if now < event.start_time else 'ended'


def generate_unique_token(length: int = 10, max_attempts: int = 100) -> str:
    """Generate collision-resistant token with safety limits."""
    for _ in range(max_attempts):
        token = get_random_string(length)
        if not VotingEvent.objects.filter(event_token=token).exists():
            return token
    raise RuntimeError("Failed to generate unique token after {max_attempts} attempts")