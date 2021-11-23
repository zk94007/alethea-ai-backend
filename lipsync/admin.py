from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget
from lipsync.models import UploadRecording, AudioCharacter, VideoCharacter, CharacterSetting, Speakers, GoogleTTS, TwoDCharacter
from lipsync.admin_forms import AudioCharacterForm, VideoCharacterForm, TwoDCharacterForm


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
        "id",
        "character",
        "type",
        "looping_video",
        "character_image",
        "gpt",
        "is_google_tts",
        "language",
        "get_demo_url"
    ]
    search_fields = ["character__speaker_name"]

    list_filter = [
        "is_google_tts"
    ]


class AdminCharacterSetting(ActivationAdmin):
    list_display = [
        "character",
        "speak_count",
        "inactivity_timeout_duration",
        "given_your_name",
        "welcome_message_prefix",
        "welcome_message_surfix",
        "type_your_name",
        "name_unavailability_title",
        "default_name",
        "end_of_interaction_response",
        "inactivity_response_required",
        "display_name_popup",
        "show_user_speech_text",
        "show_character_speech_text",
    ]
    search_fields = ["character__speaker_name"]

    list_filter = [
        "end_of_interaction_response",
        "inactivity_response_required",
        "display_name_popup",
        "show_user_speech_text",
        "show_character_speech_text",
    ]


class GoogleTTSAdmin(ActivationAdmin):
    list_display = [
        "language_name",
        "language_code",
    ]
    search_fields = ["language_name"]


class AudioCharacterAdmin(CharacterAdmin):
    form = AudioCharacterForm

    def get_queryset(self, request):
        return super(AudioCharacterAdmin, self).get_queryset(request).filter(type=AudioCharacter.AUDIO)


class VideoCharacterAdmin(CharacterAdmin):
    form = VideoCharacterForm

    def get_queryset(self, request):
        return super(VideoCharacterAdmin, self).get_queryset(request).filter(type=VideoCharacter.VIDEO)


class TwoDCharacterAdmin(CharacterAdmin):
    form = TwoDCharacterForm

    def get_queryset(self, request):
        return super(TwoDCharacterAdmin, self).get_queryset(request).filter(type=TwoDCharacter.TWODCHARACTER)


@admin.register(CharacterSetting)
class YourModelAdmin(AdminCharacterSetting):
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }


admin.site.register(UploadRecording)
admin.site.register(Speakers)
admin.site.register(GoogleTTS, GoogleTTSAdmin)
admin.site.register(AudioCharacter, AudioCharacterAdmin)
admin.site.register(VideoCharacter, VideoCharacterAdmin)
admin.site.register(TwoDCharacter, TwoDCharacterAdmin)