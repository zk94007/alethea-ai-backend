from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import ResetPasswordForm
from allauth.account.models import EmailAddress
from allauth.account.utils import setup_user_email, send_email_confirmation
from allauth.utils import email_address_exists, generate_unique_username
from django.contrib.auth import get_user_model, authenticate
from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _
from rest_auth.serializers import PasswordResetSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings
from users.models import Roles
from rest_auth.models import TokenModel

User = get_user_model()


def err_msg(field="", msg=""):
    if field is None or field == "":
        return _(msg)
    return {field: [_(msg)]}

class BlockUnBlockUser(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("is_active",)


class RolesSerializer(serializers.ModelSerializer):
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = Roles
        fields = '__all__'

    def get_role_name(self, object):
        roles_dic = {1: "User", 2: "Agent", 3: "Admin"}
        return roles_dic.get(object.user_roles, None)


class AllUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="REGISTRATION.USER_ALREADY_REGISTERED",
            )
        ]
    )

    roles = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "full_name",
            "date",
            "real_name",
            "location",
            "job_position",
            "tag_line",
            "website",
            "email",
            "password",
            "roles",
            "credit",
            "free_credit",
            "blocked",
            "is_active",
            "consent",
            "is_verified",
        ]

    def get_roles(self, object):
        return list(object.roles.all().values_list("user_roles", flat=True))

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="REGISTRATION.USER_ALREADY_REGISTERED",
            )
        ]
    )

    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "full_name",
            "date",
            "real_name",
            "location",
            "job_position",
            "tag_line",
            "website",
            "email",
            "password",
            "roles",
            "credit",
            "free_credit",
            "blocked",
            "consent",
        ]

    def get_roles(self, object):
        return list(object.roles.all().values_list("user_roles", flat=True))

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     username_field = User.EMAIL_FIELD
#
#     def validate(self, attrs):
#         data = super().validate(attrs)
        # _object = EmailAddress.objects.filter(email__exact=self.user.email)
        #
        # if _object.exists():
        #     _object = _object.first()
        #     if not _object.verified:
        #         error = err_msg(field="email", msg="Please Verify Your Account Before Login.")
        #         raise serializers.ValidationError(error)
        # else:
        #     error = err_msg(field="email", msg="Please Verify Your Account Before Login.")
        #     raise serializers.ValidationError(error)

    #     refresh = self.get_token(self.user)
    #     data['refresh'] = str(refresh)
    #     data['access'] = str(refresh.access_token)
    #     data['user'] = UserSerializer(self.user).data
    #     verification_check = EmailAddress.objects.filter(user=self.user).first()
    #     if verification_check:
    #         data['user']['is_verified'] = verification_check.verified
    #     else:
    #         data['user']['is_verified'] = False
    #     return data
    #
    # @classmethod
    # def get_token(cls, user):
    #     token = super().get_token(user)
    #     # token["user"] = {"username": user.username}
    #     return token


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "password")
        extra_kwargs = {
            "password": {"write_only": True, "style": {"input_type": "password"}},
            "email": {
                "required": True,
                "allow_blank": False,
            },
        }

    def _get_request(self):
        request = self.context.get("request")
        if (
            request
            and not isinstance(request, HttpRequest)
            and hasattr(request, "_request")
        ):
            request = request._request
        return request

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    _("A user is already registered with this e-mail address.")
                )
        return email

    def create(self, validated_data):
        user = User(
            email=validated_data.get("email"),
            username=generate_unique_username(
                [validated_data.get("email"), "user"]
            ),
        )
        user.set_password(validated_data.get("password"))
        user.save()
        request = self._get_request()
        setup_user_email(request, user, [])

        if settings.ACCOUNT_EMAIL_VERIFICATION == "mandatory":
            send_email_confirmation(request, user, signup=True)
        return user

    def save(self, request=None):
        """rest_auth passes request so we must override to accept it"""
        return super().save()


class PasswordSerializer(PasswordResetSerializer):
    """Custom serializer for rest_auth to solve reset password error"""

    password_reset_form_class = ResetPasswordForm


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class CustomTokenSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source="user", read_only=True)

    class Meta:
        model = TokenModel
        fields = ('key', "user_detail")


