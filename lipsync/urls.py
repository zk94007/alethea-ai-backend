from django.urls import path

from . import views

urlpatterns = [
    path("generate_video/<str:name>", views.GenerateVideo.as_view()),
    path("upload_file/", views.UploadFile.as_view()),
    path("upload_recording/", views.UploadRecording.as_view()),
    path("character/", views.CharacterApiView.as_view()),
    path("character_setting/", views.CharacterSettingApiView.as_view()),
]