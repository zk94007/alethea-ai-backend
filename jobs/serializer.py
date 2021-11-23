from django.contrib.auth import get_user_model
from rest_framework import serializers
from .harmfull_words import harm_full_words
from jobs.models import Job

User = get_user_model()


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get("request", None)
        limit = {User.USER: 30, User.AGENT: 300, User.ADMIN: 3000}
        validated_data.update({"user": request.user, 'limit': limit.get(request.user.roles, 0)})
        harm_full_string = harm_full_words.split(", ")
        user_credit = 0
        if request:
            user_credit = request.user.credit

        if user_credit == 0:
            raise serializers.ValidationError("JOBS.ERROR.NO_CREDIT")

        is_harmful = False
        for key in validated_data.values():
            if key in harm_full_string:
                is_harmful = True
                break

        if is_harmful:
            raise serializers.ValidationError("JOBS.ERROR.HARMFUL_DETECTION")
        else:
            return super(JobSerializer, self).create(validated_data)
