import json
import os
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand

from avatars.models import Avatar
from users.models import User


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        path_2 = os.path.join(settings.BASE_DIR, 'avatars/fixtures/initial_avataremail.json')
        f_2 = open(path_2, )
        data_2 = json.load(f_2)

        user_dict = {}
        for avatar_email in data_2:
            avatar_id = avatar_email['fields']['avatar_id']
            if avatar_id not in user_dict:
                user_dict[avatar_id] = []
            email = avatar_email['fields']['email']
            user_dict[avatar_id].append(email)

        for avatar_id, emails in user_dict.items():
            avatar = Avatar.objects.get(id=avatar_id)
            avatar.user.add(*list(User.objects.filter(email__in=emails)))

            # for email in emails:
            #     try:
            #         avatar.user.add(User.objects.get(email=email))
            #     except:
            #         continue
            avatar.save()