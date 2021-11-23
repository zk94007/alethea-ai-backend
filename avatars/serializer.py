from django.contrib.auth import get_user_model
from rest_framework import serializers

from avatars.models import Avatar

User = get_user_model()


# class AvatarEmailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AvatarEmail
#         fields = "__all__"


class AvatarSerializer(serializers.ModelSerializer):
    # emails = AvatarEmailSerializer(read_only=True, many=True)

    class Meta:
        model = Avatar
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get("request", None)
        validated_data.update({"user": request.user})
        return super(AvatarSerializer, self).create(validated_data)
