from django.contrib.auth import get_user_model
from rest_framework import serializers

from lipsync.models import UploadRecording, Character, CharacterSetting

User = get_user_model()


class UploadRecordingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = UploadRecording
        fields = '__all__'


class CharacterSettingSerializer(serializers.ModelSerializer):
    character = serializers.CharField(source='character.speaker_tts_code', read_only=True)

    class Meta:
        model = CharacterSetting
        fields = '__all__'


class CharacterSerializer(serializers.ModelSerializer):
    character_setting = CharacterSettingSerializer()
    character = serializers.CharField(source='character.speaker_tts_code', read_only=True)

    class Meta:
        model = Character
        fields = '__all__'


class GptUploadFile(serializers.Serializer):
    upload_file = serializers.FileField()
    width = serializers.CharField(max_length=255)


class PreprocessVideoSerializer(serializers.Serializer):
    video_url = serializers.URLField()
    video_id = serializers.CharField(max_length=255)
    width = serializers.CharField(max_length=255)


class GptCharacterSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=255, allow_blank=True, allow_null=True)
    session_id = serializers.CharField(max_length=255)
    user_id = serializers.CharField(max_length=255)
    user_name = serializers.CharField(max_length=255)
    frame = serializers.IntegerField(default=0)
    current_interaction = serializers.IntegerField(default=1)
    type = serializers.CharField(max_length=255, allow_blank=True, allow_null=True)
    logged_user_id = serializers.CharField(max_length=255)
    speaker = serializers.CharField(max_length=50, allow_blank=True, allow_null=True)
