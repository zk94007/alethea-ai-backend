# Generated by Django 3.2 on 2021-06-16 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gpt3', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gptcharacter',
            name='gpt_key',
            field=models.CharField(max_length=100),
        ),
    ]