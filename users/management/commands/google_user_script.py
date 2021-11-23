import json
import os
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.management.base import BaseCommand

from users.models import User


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        path = os.path.join(settings.BASE_DIR, 'users/fixtures/users.json')
        f = open(path, )
        data = json.load(f)
        for user in data:
            user_data = {}
            user_data['password'] = user.get('password', None)
            user_data['email'] = user.get('email', '')

            if user_data['password'] is None:
                try:
                    existing_user = User.objects.get(email__exact=user.get('email'))

                    google_data = {}

                    google_data['user'] = existing_user
                    google_data['user_id'] = existing_user.pk
                    google_data['provider'] = 'google'
                    google_data['uid'] = user.get('auth').get("google").get('userid')
                    google_data["extra_data"] = user
                    _, created = SocialAccount.objects.get_or_create(user=existing_user, defaults=google_data)
                except:
                    pass
