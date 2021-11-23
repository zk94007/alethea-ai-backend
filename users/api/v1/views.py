import os

from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.http import JsonResponse
from django.views import View
from rest_auth.registration.views import SocialConnectView, SocialLoginView
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
# from rest_framework_simplejwt.views import TokenObtainPairView

from users.api.v1.serializers import  AuthTokenSerializer, UserSerializer

from .custom_storage import MediaStorage


class CustomTokenObtainPairView(ObtainAuthToken):

    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        data = {}
        data['token'] = token.key
        data['user'] = UserSerializer(user).data
        verification_check = EmailAddress.objects.filter(user=user).first()
        if verification_check:
            data['user']['is_verified'] = verification_check.verified
        else:
            data['user']['is_verified'] = False
        return Response(data)

class FacebookLoginAPI(SocialLoginView):
    authentication_classes = []
    permission_classes = []
    adapter_class = FacebookOAuth2Adapter


class GoogleLoginAPI(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "https://developers.google.com/oauthplayground"

class FacebookLoginConnectAPI(SocialConnectView):
    authentication_classes = []
    permission_classes = []
    adapter_class = FacebookOAuth2Adapter


class GoogleLoginConnectAPI(SocialConnectView):
    authentication_classes = []
    permission_classes = []
    adapter_class = GoogleOAuth2Adapter


@api_view(("GET",))
@authentication_classes([])
@permission_classes(
    [
        permissions.AllowAny,
    ]
)
def generate_upload_url(request):
    content = {"please move along": "nothing to see here"}
    return Response(content, status=HTTP_200_OK)


class FileUploadView(View):
    def post(self, requests, **kwargs):
        file_obj = requests.FILES.get("file", "")

        # do your validation here e.g. file size/type check

        # organize a path for the file in bucket
        file_directory_within_bucket = "user_upload_files/{username}".format(
            username=requests.user
        )

        # synthesize a full file path; note that we included the filename
        file_path_within_bucket = os.path.join(
            file_directory_within_bucket, file_obj.name
        )

        media_storage = MediaStorage()

        if not media_storage.exists(
            file_path_within_bucket
        ):  # avoid overwriting existing file
            media_storage.save(file_path_within_bucket, file_obj)
            file_url = media_storage.url(file_path_within_bucket)

            return JsonResponse(
                {
                    "message": "OK",
                    "fileUrl": file_url,
                }
            )
        else:
            return JsonResponse(
                {
                    "message": "Error: file {filename} already exists at {file_directory} in bucket {bucket_name}".format(
                        filename=file_obj.name,
                        file_directory=file_directory_within_bucket,
                        bucket_name=media_storage.bucket_name,
                    ),
                },
                status=400,
            )
