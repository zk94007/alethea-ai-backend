from rest_framework import serializers

from gpt3.models import VaderSetting


class GptSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=255, allow_blank=True, allow_null=True)
    session_id = serializers.CharField(max_length=255)
    user_id = serializers.CharField(max_length=255)
    polite = serializers.IntegerField(default=0)
    audio_backend = serializers.CharField(max_length=255, default="selim")
    user_name = serializers.CharField(max_length=255)
    current_interaction = serializers.IntegerField(default=0)


class GptCharacterSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=255, allow_blank=True, allow_null=True)
    session_id = serializers.CharField(max_length=255)
    user_id = serializers.CharField(max_length=255)
    user_name = serializers.CharField(max_length=255)
    video_id = serializers.CharField(max_length=255)
    google_tts = serializers.IntegerField()
    gpt = serializers.IntegerField()
    language_code = serializers.CharField(max_length=255)
    language_name = serializers.CharField()
    frame = serializers.IntegerField()
    current_interaction = serializers.IntegerField(default=1)
    type = serializers.CharField(max_length=255, allow_blank=True, allow_null=True)
    logged_user_id = serializers.CharField(max_length=255)
    speaker = serializers.CharField(max_length=50, allow_null=True, allow_blank=True)

class GptPersonaSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=255)
    session_id = serializers.CharField(max_length=255)
    user_id = serializers.CharField(max_length=255)
    user_name = serializers.CharField(max_length=255)
    gender = serializers.CharField(max_length=255)
    speaker = serializers.CharField(max_length=255)
    personality_name = serializers.CharField(max_length=255)
    inft = serializers.CharField(max_length=255)
    inft_aim = serializers.CharField(max_length=255)
    characteristics = serializers.CharField(max_length=255)
    personality_trait = serializers.CharField(max_length=255)
    current_interaction = serializers.IntegerField(default=0)
    accent = serializers.CharField(max_length=255)


class GptGeneralSlackSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=255)
    session_id = serializers.CharField(max_length=255)
    user_id = serializers.CharField(max_length=255)
    polite = serializers.IntegerField(default=0)
    audio_backend = serializers.CharField(max_length=255)
    user_name = serializers.CharField(max_length=255)
    current_interaction = serializers.IntegerField(default=0)
    character = serializers.CharField(max_length=255)


class VaderSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VaderSetting
        fields = "__all__"