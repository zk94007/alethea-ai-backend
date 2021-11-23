from django.contrib.auth import get_user_model
from django.db import models
from modules.models import TimeStampModel

User = get_user_model()


class Job(TimeStampModel):
    date = models.DateField()
    mode = models.CharField(max_length=271, blank=True, null=True)
    method = models.CharField(max_length=271, blank=True, null=True)
    audio_key = models.CharField(max_length=271, blank=True, null=True)
    video_key = models.CharField(max_length=271, blank=True, null=True)
    voice_id = models.CharField(max_length=271, blank=True, null=True)
    gtts_language_code = models.CharField(max_length=271, blank=True, null=True)
    gtts_name = models.CharField(max_length=271, blank=True, null=True)
    progress = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=271, blank=True, null=True)
    result_key = models.CharField(max_length=271, blank=True, null=True)
    job_id = models.CharField(max_length=271, blank=True, null=True)
    inventory_id = models.CharField(max_length=271)
    public_id = models.CharField(max_length=271)
    text = models.CharField(max_length=271)
    animation_task_id = models.CharField(max_length=271)
    image_public_id = models.CharField(max_length=271)
    limit = models.PositiveIntegerField(default=0)
    target_video_key = models.CharField(max_length=271)
    email = models.CharField(max_length=271)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.mode
