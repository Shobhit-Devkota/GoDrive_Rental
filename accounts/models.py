import random
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def avatar_upload_path(instance, filename):
    return f"avatars/user_{instance.user.pk}/{filename}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

    @property
    def initials(self):
        name = self.user.get_full_name() or self.user.username
        parts = [p for p in name.split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return name[:2].upper()

class PasswordResetCode(models.Model):
    """A short-lived numeric code emailed to the user for the 'forgot password' flow."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    CODE_VALID_MINUTES = 15

    def __str__(self):
        return f"Reset code for {self.user.username} ({'used' if self.used else 'active'})"

    @classmethod
    def generate_for_user(cls, user):
        code = f"{random.randint(0, 999999):06d}"
        return cls.objects.create(user=user, code=code)

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=self.CODE_VALID_MINUTES)

    @property
    def is_valid(self):
        return not self.used and not self.is_expired


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)
