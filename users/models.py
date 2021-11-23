import uuid
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class Roles(models.Model):
    USER = "User"
    AGENT = "Agent"
    ADMIN = "Admin"
    ROLES = (
        (USER, "User"),
        (AGENT, "Agent"),
        (ADMIN, "Admin"),
    )

    user_roles = models.CharField(max_length=50, choices=ROLES, default=USER)


class User(AbstractUser):
    # name = models.CharField(
    #     null=True,
    #     blank=True,
    #     max_length=255,
    # )
    username = models.CharField(max_length=50, unique=False, default="", blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    real_name = models.CharField(max_length=271, blank=True, null=True)
    location = models.CharField(max_length=271, blank=True, null=True)
    job_position = models.CharField(max_length=271, blank=True, null=True)
    tag_line = models.CharField(max_length=271, blank=True, null=True)
    website = models.CharField(max_length=271, blank=True, null=True)
    roles = models.ManyToManyField(Roles)
    credit = models.PositiveIntegerField(default=0)
    free_credit = models.PositiveIntegerField(default=0)
    blocked = models.BooleanField(default=False)
    consent = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def check_password(self, raw_password):
        def setter():
            pass

        alg_prefix = "bcrypt_php$"
        password_with_alg_prefix = alg_prefix + self.password
        return check_password(raw_password, password_with_alg_prefix, setter)


class WidgetUserAccess(models.Model):
    name = models.CharField(null=True, blank=True, max_length=255)
    allowed_host = models.URLField(max_length=500)
    api_key = models.UUIDField(default=uuid.uuid4)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
