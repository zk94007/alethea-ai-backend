from django.contrib import admin

from avatars.models import Avatar


class AvatarAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "date",
        "name",
        "creator",
        "type_avatar",
        "is_public",
        "is_active",
        "is_locked",
        "email",
    ]
    search_fields = ["name"]


admin.site.register(Avatar, AvatarAdmin)
