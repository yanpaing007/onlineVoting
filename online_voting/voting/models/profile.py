import pytz
from django.db import models
from django.contrib.auth.models import User

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