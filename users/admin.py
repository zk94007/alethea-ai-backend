from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from users.models import Roles, WidgetUserAccess

from users.forms import UserChangeForm, UserCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    add_form = UserCreationForm
    fieldsets = (("User", {"fields": ("real_name", "location", "job_position", "tag_line", "website", "roles", "credit", "free_credit", "blocked", "consent")}),) + auth_admin.UserAdmin.fieldsets
    list_display = ["real_name", "is_superuser", "email"]
    search_fields = ["real_name", "email"]


class WidgetUserAccessAdmin(admin.ModelAdmin):
    list_display = ["allowed_host", "api_key", "is_active"]
    search_fields = ["allowed_host", "api_key"]
    list_filter = ["allowed_host", "api_key"]


admin.site.register(Roles)
admin.site.register(WidgetUserAccess, WidgetUserAccessAdmin)
