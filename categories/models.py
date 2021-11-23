from django.contrib.auth import get_user_model
from django.db import models
from modules.models import TimeStampModel

User = get_user_model()


class Categories(TimeStampModel):
    date = models.DateField()
    order = models.PositiveIntegerField()
    title = models.CharField(max_length=271)
    description = models.CharField(max_length=271)
    image_src = models.URLField()
    method = models.CharField(max_length=271)
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class CategoryEmail(models.Model):
    category = models.ForeignKey(
        "categories.Categories", on_delete=models.CASCADE, related_name="emails"
    )
    email = models.EmailField(max_length=271)

    def __str__(self):
        return self.email
