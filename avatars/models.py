from django.contrib.auth import get_user_model
from django.db import models

from modules.models import TimeStampModel

User = get_user_model()


class Avatar(TimeStampModel):
    date = models.DateField()
    name = models.CharField(max_length=271)
    video_key = models.CharField(max_length=271)
    image_src = models.URLField()
    # createdBy = models.CharField(max_length=271)
    # created_at = models.DateTimeField(auto_now_add=True)
    creator = models.CharField(max_length=271)
    creator_link = models.CharField(max_length=271)
    type_avatar = models.CharField(max_length=271)
    email = models.CharField(max_length=271)
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    user = models.ManyToManyField(User, null=True, blank=True)

    def __str__(self):
        return self.name
