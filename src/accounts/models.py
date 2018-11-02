from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.utils import timezone
from django.utils.crypto import get_random_string

from data.models import UserProfile


class UserProfileClaim(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def solve(self):
        # Unassign current profile.
        old_profile = self.user.profile
        old_profile.username = get_random_string(length=32)
        old_profile.user = None
        old_profile.save()

        # Assign new profile.
        self.user.profile = self.profile
        self.profile.first_name = self.user.first_name
        self.profile.last_name = self.user.last_name
        self.profile.username = self.user.username
        self.user.save()
        self.profile.save()

    def __str__(self):
        return "%d: %s claims %s" % (self.id, self.user.username, self.profile.username)