import json
import os

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        path = os.path.join(settings.BASE_DIR, 'users/fixtures/users.json')
        f = open(path, )
        data = json.load(f)
        for user in data:
            try:
                obj = EmailAddress.objects.get(user__email=user.get('email'))
                obj.verified = user.get('auth').get('email').get('valid')
                obj.save()
            except:
                pass