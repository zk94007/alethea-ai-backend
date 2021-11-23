from django.db import models
from django.contrib import admin
from django.utils.html import mark_safe
from gpt3.models import VaderSetting, GptCharacter, GptSession
from django_json_widget.widgets import JSONEditorWidget


class ActivationAdmin(admin.ModelAdmin):
    def activate(modeladmin, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = 'Activate'

    def inactivate(modeladmin, request, queryset):
        queryset.update(is_active=False)
    inactivate.short_description = 'Inactivate'

    actions = [activate, inactivate]


class CharacterAdmin(ActivationAdmin):
    list_display = [
        "character",
        "gpt_key",
        "temperature",
        "max_tokens",
        "top_p",
        "presence_penalty",
        "frequency_penalty",
        "stop_username"
    ]
    search_fields = ["character__speaker_name"]


@admin.register(GptCharacter)
class YourModelAdmin(CharacterAdmin):
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }


class SessionAdmin(admin.ModelAdmin):
    list_display = ["session", "view_conversation"]

    def view_conversation(self, obj):
        return mark_safe('<a href="/%s/%s/">%s</a>' % ('gpt/conversation', obj.id, "View Conversation"))
    view_conversation.allow_tags = True
    view_conversation.short_description = 'Conversations'


# admin.site.register(VaderSetting)
admin.site.register(GptSession, SessionAdmin)