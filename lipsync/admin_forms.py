import uuid

from django import forms

# from gpt3.models import GptCharacter
from lipsync.models import Character


class CharacterForm(forms.ModelForm):
    AUDIO = 0
    VIDEO = 1
    TWODCHARACTER = 2

    TYPE_CHOICES = (
        (AUDIO, "Audio"),
        (VIDEO, "Video"),
        (TWODCHARACTER, "2D Character"),
    )

    type = forms.Select(choices=TYPE_CHOICES)
    # gpt = forms.Select(choices=GptCharacter.objects.all())

    class Meta:
        model = Character
        fields = "__all__"


class AudioCharacterForm(CharacterForm):
    character_image = forms.ImageField(required=False)
    looping_video = forms.FileField(allow_empty_file=True, required=False)

    class Meta:
        model = Character
        exclude = ("type", "talking_video", "waiting_video",)

    def __init__(self, *args, **kwargs):
        super(CharacterForm, self).__init__(*args, **kwargs)
        self.type = Character.AUDIO

    def clean(self):
        validated_data = super(AudioCharacterForm, self).clean()
        character_image = validated_data.get("character_image")
        looping_video = validated_data.get("looping_video")
        if character_image and looping_video:
            raise forms.ValidationError(
                {"looping_video": ["Please select either character_image or looping_video."]},
                {"character_image": ["Please select either character_image or looping_video."]}
            )


class VideoCharacterForm(CharacterForm):
    looping_video = forms.FileField(allow_empty_file=True, required=False)

    class Meta:
        model = Character
        exclude = ("type", "character_image", "talking_video", "waiting_video",)

    def __init__(self, *args, **kwargs):
        super(CharacterForm, self).__init__(*args, **kwargs)
        self.type = Character.VIDEO


class TwoDCharacterForm(CharacterForm):
    waiting_video = forms.FileField(allow_empty_file=True, required=False)
    talking_video = forms.FileField(allow_empty_file=True, required=False)

    class Meta:
        model = Character
        exclude = ("type", "looping_video", "character_image",)

    def __init__(self, *args, **kwargs):
        super(CharacterForm, self).__init__(*args, **kwargs)
        self.type = Character.TWODCHARACTER


