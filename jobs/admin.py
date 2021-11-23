from django.contrib import admin

from jobs.models import Job


class JobAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "date",
        "mode",
        "method",
        "audio_key",
        "video_key",
        "voice_id",
        "gtts_language_code",
        "gtts_name",
        "progress",
        "status",
        "result_key",
        "job_id",
        "inventory_id",
        "public_id",
        "text",
        "animation_task_id",
        "image_public_id",
        "limit",
        "target_video_key",
        "email",
    ]
    search_fields = ["order"]


admin.site.register(Job, JobAdmin)
