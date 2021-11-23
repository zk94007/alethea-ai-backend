"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from allauth.account.views import confirm_email
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.inspectors import view
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_swagger.views import get_swagger_view

from users.views import complete_view

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path('registration/complete/', complete_view, name='account_confirm_complete'),
    url(r'^user/register/account-confirm-email/(?P<key>[-:\w]+)/$', confirm_email,
        name='account_confirm_email'),  # Done
    path("admin/", admin.site.urls),
    path("users/", include("users.urls", namespace="users")),
    path("jobs/", include("jobs.urls")),
    path("avatars/", include("avatars.urls")),
    path("categories/", include("categories.urls")),
    path("gpt/", include("gpt3.urls")),
    path("lipsync/", include("lipsync.urls")),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path(
        "api/v1/",
        include(
            [
                path("auth/", include("rest_auth.urls")),
                path("", include("users.api.v1.urls")),
            ]
        ),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # swagger
    api_info = openapi.Info(
        title="AletheaAI API",
        default_version="v1",
        description="API documentation for AletheaAI",
    )

    schema_view = get_schema_view(
        api_info,
        public=True,
        permission_classes=(permissions.IsAdminUser, ),
    )

    urlpatterns += [
        path(
            "api-docs/",
            login_required(schema_view.with_ui("swagger", cache_timeout=0)),
            name="api_docs",
        )
    ]

    urlpatterns += [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ]