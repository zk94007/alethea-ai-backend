# Generated by Django 3.2 on 2021-04-28 19:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Avatar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('name', models.CharField(max_length=271)),
                ('video_key', models.CharField(max_length=271)),
                ('image_src', models.URLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('creator', models.CharField(max_length=271)),
                ('type_avatar', models.CharField(max_length=271)),
                ('email', models.CharField(max_length=271)),
                ('is_public', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('is_locked', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AvatarEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=271)),
                ('avatar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emails', to='avatars.avatar')),
            ],
        ),
    ]