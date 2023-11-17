# Generated by Django 4.2.7 on 2023-11-17 11:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("story", "0006_story_like_count"),
        ("user", "0003_recentstory_user_recent_stories"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserStoryTimeStamp",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="TTime Stamp"
                    ),
                ),
                (
                    "story",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="timestamps",
                        to="story.story",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="user",
            name="recent_stories",
        ),
        migrations.DeleteModel(
            name="RecentStory",
        ),
        migrations.AddField(
            model_name="userstorytimestamp",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="timestamps",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]