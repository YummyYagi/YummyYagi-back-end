# Generated by Django 4.2.7 on 2023-11-08 20:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('story', '0004_story_hate_count_story_hidden'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='story',
            name='hidden',
        ),
    ]
