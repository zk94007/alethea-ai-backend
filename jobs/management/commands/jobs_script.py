import json
import os
import datetime
from django.conf import settings
from django.core.management.base import BaseCommand

from jobs.models import Job
from users.models import User


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        path = os.path.join(settings.BASE_DIR, 'jobs/fixtures/jobs.json')
        f = open(path, )
        data = json.load(f)
        for job in data:
            jobs_data = {}
            try:
                jobs_data['date'] = datetime.datetime.strptime(job['date']["$date"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
            except:
                continue
            jobs_data['mode'] = job.get("renderData", {}).get('mode', '')
            jobs_data['method'] = job.get("renderData", {}).get('method', '')
            jobs_data['audio_key'] = job.get("renderData", {}).get('audioKey', '')
            jobs_data['video_key'] = job.get("renderData", {}).get('videoKey', '')
            jobs_data['progress'] = job.get("renderData", {}).get('progress', 0)
            jobs_data['result_key'] = job.get("renderData", {}).get('resultKey', '')
            jobs_data['job_id'] = job.get("renderData", {}).get('jobId', '')
            jobs_data['inventory_id'] = job.get("renderData", {}).get('inventoryId', '')
            jobs_data['public_id'] = job.get("renderData", {}).get('publicId', '')
            jobs_data['text'] = job.get("renderData", {}).get('text', '')
            jobs_data['status'] = job.get("renderData", {}).get('status', '')
            jobs_data["image_public_id"] = job.get("renderData", {}).get('imageKey', '')
            jobs_data['email'] = job.get('email')

            job_user = User.objects.filter(email__exact=job.get('email'))
            if job_user:
                jobs_data['user'] = job_user.first()

            try:
                Job.objects.create(**jobs_data)
            except:
                continue
