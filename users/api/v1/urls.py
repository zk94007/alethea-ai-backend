from django.urls import include, path
from rest_framework.routers import DefaultRouter
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
#     TokenVerifyView,
# )
from rest_framework.authtoken import views

from users.api.v1.views import *
from users.api.v1.viewsets import BlockUser, SignupViewSet, UnBlockUser, UserViewSet


from .views import (
    CustomTokenObtainPairView,
    FacebookLoginAPI,
    FacebookLoginConnectAPI,
    FileUploadView,
    GoogleLoginAPI,
    GoogleLoginConnectAPI,
    generate_upload_url,
)

router = DefaultRouter()
router.register("signup", SignupViewSet, basename="signup")
router.register("user", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    path('login/', CustomTokenObtainPairView.as_view()),
    # path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    # path("login/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # path("login/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Social Login
    path("login/social/google/", GoogleLoginAPI.as_view(), name="google_login"),
    path(
        "login/social/google/connect/",
        GoogleLoginConnectAPI.as_view(),
        name="google_login_connect",
    ),
    path("login/social/facebook/", FacebookLoginAPI.as_view(), name="facebook_login"),
    path(
        "login/social/facebook/connect/",
        FacebookLoginConnectAPI.as_view(),
        name="facebook_login_connect",
    ),
    path("block/<int:pk>/", BlockUser.as_view(), name="block_user"),
    path("un_block/<int:pk>/", UnBlockUser.as_view(), name="un_block_user"),
    path("generate-upload-url", generate_upload_url, name="generate_upload_url"),
    path("file-upload", FileUploadView.as_view(), name="file_upload"),
]
