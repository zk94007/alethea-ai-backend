import json
import os
import datetime

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.core.management.base import BaseCommand

from users.models import Roles, User


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        path = os.path.join(settings.BASE_DIR, 'users/fixtures/users.json')
        f = open(path, )
        data = json.load(f)
        for user in data:
            user_data = {}
            try:
                user_data['date'] = datetime.datetime.strptime(user['date']["$date"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
            except:
                continue
            user_data['real_name'] = user.get('realname', '')
            user_data['tag_line'] = user.get('tagline', '')
            user_data['website'] = user.get('website', '')
            user_data['consent'] = user.get('consent', False)
            user_data['credit'] = user.get('credit', 0)
            user_data['email'] = user.get('email', '')
            user_data['password'] = user.get('password', '')

            try:
                new_user = User.objects.create(**user_data)
            except:
                continue

            for role in user['roles']:
                new_user.roles.add(Roles.objects.get(user_roles=role))

            new_user.save()
            try:
                EmailAddress.objects.get_or_create(email=new_user.email, user=new_user, verified=True, primary=True)
            except:
                pass