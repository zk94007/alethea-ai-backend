import shutil
import uuid, wget
import os
import subprocess
import json
import requests
from time import time
from rest_framework import generics
from shutil import copyfile

from rest_framework.response import Response
from google.cloud import texttospeech

from lipsync.serializer import GptUploadFile, PreprocessVideoSerializer, GptCharacterSerializer
from lipsync.video_preprocessor import preprocess_video
from utils.gpt3_functions import gpt3_request
from lipsync.models import UploadRecording, Character, CharacterSetting
from lipsync.serializer import UploadRecordingSerializer, CharacterSerializer, CharacterSettingSerializer

# Allowed video formats
from server.settings import BASE_DIR

ALLOWED_EXTENSIONS = {'mp4'}

# HOST URL where video is saving
HOST_URL = f'https://backend-lipsync.alethea.ai'

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


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_gpt2_message(prompt, gpt):
    url_list = ['34.71.237.248:8081', '34.71.237.248:8082', '35.184.183.110:8081']
    endpoint = url_list[gpt]

    prompt = prompt.replace("'", "")
    command = f"curl --location --request POST '{endpoint}/generate' --form 'conversation={prompt}' "
    print("COMMAND ===================== ", command)
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    print("============= out & err ===================\n", out, err)
    return json.loads(out).get("response")


def get_gpt3_response(request, type_character):

    response = gpt3_request(request, type_character)

    for c in response.data.get('choices'):
        return c.get("text"), c.get("raw_text")


def download_file(url, local_filename, text, speaker):
    payload = {
        'text': text,
        'length_scale': '1.0',
        'noise_scale': '0.55',
        'length_scale': '1.1',
        'noise_scale': '0.33',
        'sigma': '0.88',
        'denoiser_scale': '0.07',
        'speaker': speaker
    }

    files = [

    ]
    headers = {}

    with requests.post(url, headers=headers, data=payload, files=files, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename


class PreprocessVideo(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = PreprocessVideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        req_pr = serializer.data
        video_url = req_pr['video_url']
        video_id = req_pr['video_id']
        width = req_pr['width']
        if video_url:
            video_id = uuid.uuid4().hex[:7]
            os.makedirs(f'preprocessed_data/{video_id}')
            wget.download(video_url, f'preprocessed_data/{video_id}/video.mp4')
        preprocess_video(video_id, width)
        return Response({'video_id': video_id})


class UploadRecording(generics.ListCreateAPIView):
    queryset = UploadRecording.objects.all()
    serializer_class = UploadRecordingSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CharacterApiView(generics.ListAPIView):
    queryset = Character.objects.none()
    serializer_class = CharacterSerializer

    def get_queryset(self):
        queryset = Character.objects.filter(is_active=True)
        character = self.request.query_params.get("character")
        if character:
            queryset = queryset.filter(character__speaker_tts_code__exact=character)
        return queryset


class CharacterSettingApiView(generics.ListAPIView):
    queryset = CharacterSetting.objects.none()
    serializer_class = CharacterSettingSerializer

    def get_queryset(self):
        queryset = Character.objects.all()
        character = self.request.query_params.get("character")
        if character:
            queryset = queryset.filter(character__speaker_tts_code__exact=character)
        return queryset


class UploadFile(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = GptUploadFile(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = request.FILES.get("upload_file")
        if uploaded_file and uploaded_file.name != '':
            if uploaded_file and allowed_file(uploaded_file.name):
                video_id = uuid.uuid4().hex[:7]
                width = request.data.get("width")
                path = f'preprocessed_data/{video_id}/'
                os.makedirs(path)
                video_path = os.path.join(path, 'video.mp4')
                # uploaded_file.save(video_path)
                open(video_path, 'wb').write(uploaded_file.file.read())
                copyfile(video_path, os.path.join(f'static/{video_id}.mp4', ))
                try:
                    preprocess_video(video_id, width=width)
                except Exception as e:
                    error = str(e)
                    print(error)
                response = {"video_id": video_id, "video_url": f'{HOST_URL}/{VIDEO_DIR_NAME}/{video_id}.mp4'}
                return Response(response, status=200)
            return Response(f"Not a valid video format allowed formats are: {ALLOWED_EXTENSIONS}")
        return Response("no video found")


class GenerateVideo(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        type_character = kwargs['name']
        serializer = GptCharacterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        req_pr = serializer.data
        response = Character.objects.get(character_name=type_character).generate_video(req_pr)
        return Response(response)