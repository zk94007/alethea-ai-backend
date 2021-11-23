from django.db import models


class TimeStampModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
