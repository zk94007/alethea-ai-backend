"""
Django settings for server project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import logging
import os
from datetime import timedelta
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

environ.Env.read_env()

DB_HOST = env.str("DB_HOST")
DB_NAME = env.str("DB_NAME")
DB_USER = env.str("DB_USER")
DB_PASSWORD = env.str("DB_PASSWORD")
DB_PORT = env.str("DB_PORT")
if 'RDS_DB_NAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

# ALLOWED_HOSTS = env.list("HOST", default=["https://backend-develop.alethea.ai", "https://backend-demo.alethea.ai"])

ALLOWED_HOSTS = [
                    "localhost",
                    "127.0.0.1",
                    "backend-develop.alethea.ai",
                    "backend-demo.alethea.ai",
                    "drf-develop.alethea.ai",
                    "ec2-3-143-225-21.us-east-2.compute.amazonaws.com"
                 ]


# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT = env.bool("SECURE_REDIRECT", default=False)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "users",
    "jobs",
    "avatars",
    "categories",
    "gpt3",
    "lipsync",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_swagger",
    "rest_framework.authtoken",
    "rest_auth.registration",
    "allauth",
    "allauth.account",
    "django_extensions",
    "drf_yasg",
    "ckeditor",
    "django_json_widget",
    "rest_auth",
    "corsheaders",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    "django_bcrypt",
]

INSTALLED_APPS += THIRD_PARTY_APPS

AUTH_USER_MODEL = "users.User"
SITE_ID = 1

PASSWORD_HASHERS = [
    'users.hashers.hashers.BCryptPasswordHasher',
]

# For all origin mark as True
# CORS_ALLOW_ALL_ORIGINS = True

# CORS_ALLOW_HEADERS = ['*']

# for limited allow origins add in list and uncomment it
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1",
    "https://backend-develop.alethea.ai",
    "https://backend-demo.alethea.ai",
    "https://drf-develop.alethea.ai"
]

CORS_ORIGIN_WHITELIST = [
    "http://localhost",
    "http://127.0.0.1",
    "https://backend-develop.alethea.ai",
    "https://backend-demo.alethea.ai",
    "https://drf-develop.alethea.ai"
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'app_platform'
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "server.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_ROOT = BASE_DIR / "static/"
STATIC_URL = "/static/"
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [BASE_DIR / "staticfiles"]


AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

LOGIN_URL = '/admin/'
LOGOUT_URL = '/admin/'
LOGIN_REDIRECT_URL = '/admin/'

# allauth / users
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
ACCOUNT_UNIQUE_EMAIL = True
LOGIN_REDIRECT_URL = reverse_lazy('account_confirm_complete')
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = reverse_lazy('account_confirm_complete')
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = reverse_lazy('account_confirm_complete')

ACCOUNT_ADAPTER = "users.adapters.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "users.adapters.SocialAccountAdapter"
ACCOUNT_ALLOW_REGISTRATION = env.bool("ACCOUNT_ALLOW_REGISTRATION", True)
SOCIALACCOUNT_ALLOW_REGISTRATION = env.bool("SOCIALACCOUNT_ALLOW_REGISTRATION", True)


# Facebook login keys
SOCIALACCOUNT_PROVIDERS = {
    "facebook": {
        "SCOPE": ["email", "public_profile", "user_friends"],
        "FIELDS": [
            "id",
            "email",
            "name",
            "first_name",
            "last_name",
        ],
    },
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# JWT Time
# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
# }

# REST_USE_JWT = True

# Rest Framework Settings
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        'rest_framework.authentication.TokenAuthentication',
        "rest_framework.authentication.SessionAuthentication",
        # "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/day", "user": "1000/day"},
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
}

REST_AUTH_SERIALIZERS = {
    # Replace password reset serializer to fix 500 error
    "PASSWORD_RESET_SERIALIZER": "users.api.v1.serializers.PasswordSerializer",
    "USER_DETAILS_SERIALIZER": "users.api.v1.serializers.UserSerializer",
    "TOKEN_SERIALIZER": "users.api.v1.serializers.CustomTokenSerializer",

}

REST_AUTH_REGISTER_SERIALIZERS = {
    # Use custom serializer that has no username and matches web signup
    "REGISTER_SERIALIZER": "users.api.v1.serializers.SignupSerializer",
}


# Swagger settings for api docs
SWAGGER_SETTINGS = {
    "DEFAULT_INFO": f"{ROOT_URLCONF}.api_info",
}

# Email settings
EMAIL_HOST = env.str("EMAIL_HOST", "smtp.sendgrid.net")
EMAIL_HOST_USER = env.str("SENDGRID_USERNAME", "")
EMAIL_HOST_PASSWORD = env.str("SENDGRID_PASSWORD", "")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
if DEBUG or not (EMAIL_HOST_USER and EMAIL_HOST_PASSWORD):
    # output email to console instead of sending
    if not DEBUG:
        logging.warning(
            "You should setup `SENDGRID_USERNAME` and `SENDGRID_PASSWORD` env vars to send emails."
        )
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# Debug toolbar settings
if DEBUG:

    INSTALLED_APPS += [
        "debug_toolbar",
    ]

    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
    INTERNAL_IPS = [
        "127.0.0.1",
    ]

    DEBUG_TOOLBAR_CONFIG = {
        "INTERCEPT_REDIRECTS": False,
    }

# DEFAULT_FILE_STORAGE = "users.api.v1.custom_storage.MediaStorage"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"

AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN")
AWS_CLOUDFRONT_KEY = env.str("AWS_CLOUDFRONT_KEY", None, multiline=True).encode("ascii")
AWS_CLOUDFRONT_KEY_ID = os.environ.get("AWS_CLOUDFRONT_KEY_ID", None)

GPT3_KEY = env.str("GPT3_KEY")
GPT3_KEY_RON_ALICE = env.str("GPT3_KEY_RON_ALICE")
REPLICA_KEY = env.str("REPLICA_KEY")
REPLICA_STUDIOS_AUTH = env.str("REPLICA_STUDIOS_AUTH")
REPLICA_STUDIOS_SPEECH = env.str("REPLICA_STUDIOS_SPEECH")
REPLICA_USERNAME = env.str("REPLICA_USERNAME")
REPLICA_PASSWORD = env.str("REPLICA_PASSWORD")
SLACK_TOKEN = env.str("SLACK_TOKEN")
GPT3_OPEN_AI_DAVINCI_URL = env.str("GPT3_OPEN_AI_DAVINCI_URL")
GPT3_OPEN_AI_DAVINCI_INSTRUCT_BETA_URL = env.str("GPT3_OPEN_AI_DAVINCI_INSTRUCT_BETA_URL")
GPT3_OPEN_AI_FILTER_ALPHA_URL = env.str("GPT3_OPEN_AI_FILTER_ALPHA_URL")
ALETHEA_SYNTH_META = env.str("ALETHEA_SYNTH_META")