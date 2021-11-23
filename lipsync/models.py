import os
import uuid
from shutil import copyfile
from time import time

import cv2
import requests

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.files import File
from django.db import models
from django.utils.safestring import mark_safe

from lipsync.triton_inference import process
from lipsync.video_preprocessor import preprocess_video
from modules.models import TimeStampModel
from gpt3.models import GptCharacter, Speakers

from google.cloud import texttospeech
from django.contrib.postgres.fields import JSONField

# HOST URL where video is saving
from server.settings import BASE_DIR
from utils.gpt3_functions import replica_tts, create_folder

HOST_URL = f'http://ec2-3-143-225-21.us-east-2.compute.amazonaws.com'
HOSTNAME = os.getenv('HOSTNAME')

# Video Directory name
VIDEO_DIR_NAME = 'static'

# Create if Video Directory not found.
publicDirectory = os.path.join(BASE_DIR, VIDEO_DIR_NAME)
if not os.path.exists(publicDirectory):
    os.makedirs(publicDirectory)

client = texttospeech.TextToSpeechClient()
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16
)

User = get_user_model()

project_path = os.path.abspath(os.getcwd())


def gpt_file_folder_path(folder_name):
    folder_path = project_path + '/media/preprocessed_data/' + folder_name
    return folder_path


def get_upload_path(instance, file_name):
    return "%s/%s" % (gpt_file_folder_path(instance.character.speaker_tts_code), file_name)


class UploadRecording(TimeStampModel):
    file_upload = models.FileField(upload_to='static/')
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class GoogleTTS(TimeStampModel):
    language_code = models.CharField(max_length=50, default="en-US")
    language_name = models.CharField(max_length=50)

    def __str__(self):
        return self.language_name

    class Meta:
        verbose_name_plural = "Google TTS"


class Character(TimeStampModel):
    AUDIO = 0
    VIDEO = 1
    TWODCHARACTER = 2

    TYPE_CHOICES = (
        (AUDIO, "Audio"),
        (VIDEO, "Video"),
        (TWODCHARACTER, "2D Character"),
    )
    character_name = models.CharField(max_length=50)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    character = models.ForeignKey(Speakers, on_delete=models.CASCADE, related_name="gpt_speaker_name",
                                  limit_choices_to={"is_active": True})
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default=VIDEO)
    looping_video = models.FileField(upload_to=get_upload_path, blank=True, null=True)
    character_image = models.ImageField(upload_to='character_images/', blank=True, null=True)
    waiting_video = models.FileField(upload_to='waiting_video/', blank=True, null=True)
    talking_video = models.FileField(upload_to='talking_video/', null=True, blank=True)
    gpt = models.OneToOneField(GptCharacter, on_delete=models.CASCADE, related_name="gpt_character")
    is_google_tts = models.BooleanField(default=False)
    language = models.ForeignKey(GoogleTTS, on_delete=models.CASCADE, related_name="language")

    class Meta:
        verbose_name_plural = "Characters"

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        instance = super(Character, self).save(force_insert=force_insert, force_update=force_update,
                                       using=using, update_fields=update_fields)

        if self.type == Character.VIDEO:
            preprocess_video(self.looping_video.url.replace("/media/", "/", 1), width=None)

    def get_site_url(self):
        domain = Site.objects.get_current().domain
        url = 'http://{domain}'.format(domain=domain)
        return url

    @property
    def get_demo_url(self):
        return mark_safe(
            f"<a href='{self.get_site_url()}/character/{self.character.speaker_tts_code}'>{self.get_site_url()}/character/{self.character.speaker_tts_code}</a>")

    def __str__(self):
        return self.character.speaker_name

    def get_gpt3_response(self, request):

        response = GptCharacter.objects.filter(character__speaker_tts_code__exact=self.character.speaker_tts_code).first().gpt3_request(
            request)

        if self.type == Character.AUDIO:
            return response.get("text"), response.get("raw_text")
        else:
            for c in response.data.get('choices'):
                return c.get("text"), c.get("raw_text")

    def google_tts(self, text, language_name, language_code):
        audio_file = f"audio_files/{uuid.uuid4().hex[:7]}.wav"

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            name=language_name, language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        with open(audio_file, "wb") as out:
            out.write(response.audio_content)
        return {"url": f"{HOSTNAME}/{audio_file}"}

    def selim_tts(self, text, speaker="darth_v2"):
        print("\n\nSpeaker is => ", speaker)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if speaker == "alice":
            data = {
                'text': text,
                'length_scale': '1.05',
                'noise_scale': '0.56',
                'sigma': '0.89',
                'denoiser_scale': '0.02',
                'speaker': speaker
            }
        elif speaker == "gmoney":
            data = {
                'text': text,
                'length_scale': '1.05',
                'noise_scale': '0.46',
                'sigma': '0.89',
                'denoiser_scale': '0.2',
                'speaker': speaker
            }
        elif speaker == "metakovan":
            data = {
                'text': text,
                'length_scale': '1.05',
                'noise_scale': '0.667',
                'noise_w_scale': '0.8',
                'speaker': speaker
            }
        else:
            data = {
                'text': text,
                'length_scale': '1.0',
                'noise_scale': '0.333',
                'sigma': '0.88',
                'denoiser_scale': '0.07',
                'speaker': speaker
            }

        if speaker == "metakovan":
            try:
                response = requests.post("https://tts.alethea.ai/api/synth-vits-meta-single", data=data)
            except Exception as e:
                print("=======exception===========", e)
        else:
            response = requests.post("http://18.118.209.78:5003/api/synth-meta", data=data, headers=headers)
        # print("================ ", response.content, response)
        return response.json()

    def replica_response(self, res, req_pr):
        current_interaction = req_pr['current_interaction']
        audio_backend = req_pr.get('audio_backend', 'selim')
        language_code = req_pr.get('language_code', "en-US")
        language_name = req_pr.get('language_name', "en-US-Wavenet-C")
        speaker = req_pr.get("speaker", "darth_v2")

        text = ""
        raw_text = ""
        for c in res.get('choices'):
            text = c.get("text", "")
            raw_text = c.get("raw_text", "")
        if audio_backend == "selim":
            response = self.selim_tts(text, speaker)
        elif audio_backend == "google_tts":
            response = self.google_tts(text, language_name, language_code)
        else:
            response = replica_tts(text)

        response.update({"txt": text, "raw_text": raw_text})
        return response

    def generate_video(self, req_pr):
        text = req_pr['prompt']
        raw_text = text
        start = time()
        gpt3_esponse = GptCharacter.objects.filter(
            character__speaker_tts_code__exact=self.character.speaker_tts_code).first().gpt3_request(req_pr)
        google_tts = self.is_google_tts
        cur_frame = req_pr['frame']

        gpt3_time = round(time() - start, 3)
        request_id = uuid.uuid4().hex[:7]
        audio_file = f"temp/{request_id}.wav"

        audio_backend = req_pr.get('audio_backend', 'selim')
        speaker = req_pr.get("speaker", "darth_v2")
        request_id = uuid.uuid4().hex[:7]

        try:
            color_transfer = bool(int(req_pr.get('color_transfer')))
        except:
            color_transfer = None

        tts_time = round(time() - start - gpt3_time, 3)
        times = {}
        times['tts'] = tts_time
        times['gpt3'] = gpt3_time
        times['total'] = round(time() - start, 3)
        frame_shift = times['total'] * 25

        if google_tts:
            language_code = self.language.language_code
            language_name = self.language.language_name
            synthesis_input = texttospeech.SynthesisInput(text=raw_text)
            voice = texttospeech.VoiceSelectionParams(
                name=language_name, language_code=language_code,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )

            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
            with open(audio_file, "wb") as out:
                out.write(response.audio_content)

        else:
            if self.type == Character.VIDEO:
                gpt3_response = self.replica_response(gpt3_esponse.data, req_pr)
                video_path = self.looping_video.url.replace("/media/", "/", 1)
                audio_file_url = gpt3_response.get('url').rsplit('/', 1)[1]
                copyfile(f"/sharedVolume/{audio_file_url}", audio_file)
                result_vid_path, times, estimated_frames = process(self.character.speaker_tts_code, audio_file_url, video_path, cur_frame, color_transfer)
                response = {"result_video_url": f'{HOST_URL}/{result_vid_path}', "text": raw_text,
                            "time_taken_by_functions": times}
                # response = {"url": 'https://apologia.ai/static/37e7d4e.mp4',
                #             "txt": gpt3_esponse.data.get('choices')[0].get('raw_text'),
                #             "time_taken_by_functions": times}
            else:
                gpt3_response = self.replica_response(gpt3_esponse.data, req_pr)
                response = {"url": gpt3_response.get('url'), "txt": gpt3_response.get('txt'),
                            "time_taken_by_functions": times}

        return response


class AudioCharacter(Character):
    def __init__(self, *args, **kwargs):
        self._meta.get_field('type').default = Character.AUDIO
        super(AudioCharacter, self).__init__(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Audio character"


class VideoCharacter(Character):
    def __init__(self, *args, **kwargs):
        self._meta.get_field('type').default = Character.VIDEO
        super(VideoCharacter, self).__init__(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "Video character"


class TwoDCharacter(Character):
    def __init__(self, *args, **kwargs):
        self._meta.get_field('type').default = Character.TWODCHARACTER
        super(TwoDCharacter, self).__init__(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = "2D Character"


class CharacterSetting(TimeStampModel):
    character = models.ForeignKey(Speakers, on_delete=models.CASCADE, related_name="speaker_setting",
                                  limit_choices_to={"is_active": True})
    gpt = models.OneToOneField(Character, on_delete=models.CASCADE, related_name="character_setting")
    speak_count = models.IntegerField(default=10)
    inactivity_timeout_duration = models.IntegerField(default=1500)
    given_your_name = models.CharField(max_length=255, default="What is your name ?")
    welcome_message_prefix = models.CharField(max_length=255, default="Welcome")
    welcome_message_surfix = models.CharField(max_length=255,
                                              default=" please enable sound and mic to begin your interaction.")
    type_your_name = models.CharField(max_length=255, default="Please type your name, and press Next")
    name_unavailability_title = models.CharField(max_length=255,
                                                 default="We have not come across that name before, is it ok if it calls you:")
    default_name = models.CharField(max_length=255, default="My Young Apprentice")
    end_of_interaction_response = models.BooleanField(default=False)
    inactivity_response_required = models.BooleanField(default=False)
    random_responses = JSONField(null=True, blank=True)
    inactivity_response = JSONField(null=True, blank=True)
    display_name_popup = models.BooleanField(default=True)
    show_user_speech_text = models.BooleanField(default=True)
    show_character_speech_text = models.BooleanField(default=True)

    def __str__(self):
        return self.character.speaker_name

    class Meta:
        verbose_name_plural = "Character Setting"
