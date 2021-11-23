from django.urls import path

from . import views

urlpatterns = [
    path("gpt3_api/", views.Gpt3ApiView.as_view()),
    path("gpt3_api_vader/", views.Gpt3ApiVaderView.as_view()),
    path("gpt3_api_persona/", views.PersonaApi.as_view()),
    path("v1/gpt3_api/<str:name>", views.Gpt3Api.as_view()),
    path("speech/generate/", views.GenerateSpeechApi.as_view()),
    path("post_on_slack/", views.PostSlackApi.as_view()),
    path("vader_setting/", views.AvadarSettingListApi.as_view()),
    path("conversation/<int:pk>/", views.conversations),
]