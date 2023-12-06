from django.test import TestCase
from user.models import User
from .models import Story, Content, Comment
from django.conf import settings
from django.urls import reverse
from user.serializers import LoginSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class StoryTests(TestCase):
    @classmethod
    # 셋업
    def setUpTestData(cls):
        member = {
            "email": "testuser@email.com",
            "nickname": "testuser",
            "country": "미국",
            "password": "1234567!",
        }
        cls.user = User.objects.create_user(**member)
        cls.user.is_active = True
        cls.user.save()
        response = LoginSerializer(data=member)
        try:
            response.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        cls.access_token = response.validated_data["access"]
        cls.story = Story.objects.create(author=cls.user, title="test")
        cls.content = Content.objects.create(
            story=cls.story, paragraph="1", image="story/test1.jpg"
        )

    def post_story_view_test(self):
        response = self.client.post(
            reverse("story_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={
                "title": "testing",
                "paragraph_list": ["1", "2", "3"],
                "image_url_list": [
                    "https://sunny/?src=https%3A%2F%2Fi.pinimg.com%2Foriginals%2F58%2F3c%2F5e%2F583c5e88e997d03e49842aff1719aa66.jpg&type=a340",
                    "None",
                    "https://search.pstatic.net/common/?src=http%3A%2F%2Fblogfiles.naver.net%2FMjAyMTA1MjNfNDYg%2FMDAxNjIxNzc5MTQzNDMz.XmG1Qj7VYlzyju91hKTVzHnZGWAuxmcLqB7YD52yYhAg.RoIKKFGBrBW3T1vMPwEiaEzQK6MkUEhCp_2-K7jscdwg.JPEG.kanghjj2002%2FScreenshot%25A3%25DF20210523%25A3%25AD231207%25A3%25DFHABL.jpg&type=a340",
                ],
            },
        )
        self.assertEqual(response.status_code, 201)

    def get_main_page_test(self):
        response = self.client.get(
            reverse("story_view"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["story_list"][0]["author_nickname"],
            self.story.author.nickname,
        )
        self.assertEqual(
            response.data["story_list"][0]["story_title"], self.story.title
        )
        self.assertEqual(
            response.data["story_list"][0]["content"],
            {
                "story_paragraph": self.content.paragraph,
                "story_image": self.content.image.url,
            },
        )
        self.assertEqual(
            response.data["story_list"][0]["author_country"], self.story.author.country
        )

    def get_detail_page_test(self):
        id = self.story.id
        url = reverse("detail_page_view", kwargs={"story_id": id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["detail"]["author_nickname"], self.story.author.nickname
        )
        self.assertEqual(response.data["detail"]["story_title"], self.story.title)
        test_paragraph = response.data["detail"]["story_paragraph_list"][0]
        self.assertEqual(test_paragraph["paragraph"], self.content.paragraph)
        self.assertEqual(test_paragraph["story_image"], self.content.image.url)

    def delete_story_test(self):
        id = self.story.id
        response = self.client.delete(
            reverse("detail_page_view", kwargs={"story_id": id}),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 204)


class CommentTests(TestCase):
    @classmethod
    # 셋업
    def setUpTestData(cls):
        member = {
            "email": "testuser@email.com",
            "nickname": "testuser",
            "country": "미국",
            "password": "1234567!",
        }
        cls.user = User.objects.create_user(**member)
        cls.user.is_active = True
        cls.user.save()
        response = LoginSerializer(data=member)
        try:
            response.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        cls.access_token = response.validated_data["access"]
        cls.story = Story.objects.create(author=cls.user, title="test")
        cls.content = Content.objects.create(
            story=cls.story, paragraph="1", image="story/test1.jpg"
        )
        cls.comment = Comment.objects.create(
            author=cls.user, story=cls.story, content="hi"
        )

    def post_comment_test(self):
        id = self.story.id
        response = self.client.post(
            reverse("comment_view", kwargs={"story_id": id}),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={"content": "hello"},
        )
        self.assertEqual(response.status_code, 201)

    def get_comment_test(self):
        response = self.client.get(
            reverse("comment_view", kwargs={"story_id": self.story.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={"content": "hello"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["comments"][0]["story_id"], self.story.id)
        self.assertEqual(
            response.data["comments"][0]["comment_id"], str(self.comment.id)
        )
        self.assertEqual(
            response.data["comments"][0]["author_id"], str(self.comment.author.id)
        )
        self.assertEqual(
            response.data["comments"][0]["author_nickname"],
            self.comment.author.nickname,
        )
        self.assertEqual(
            response.data["comments"][0]["author_image"],
            self.comment.author.profile_img.url,
        )
        self.assertEqual(response.data["comments"][0]["content"], self.comment.content)

    def delete_comment_test(self):
        response = self.client.delete(
            reverse(
                "comment_delete_view",
                kwargs={"story_id": self.story.id, "comment_id": self.comment.id},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 204)


class LikeHateBookMarkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        member = {
            "email": "testuser@email.com",
            "nickname": "testuser",
            "country": "미국",
            "password": "1234567!",
        }
        cls.user = User.objects.create_user(**member)
        cls.user.is_active = True
        cls.user.save()
        response = LoginSerializer(data=member)
        try:
            response.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        cls.access_token = response.validated_data["access"]
        cls.story = Story.objects.create(author=cls.user, title="test")

    def like_story_test(self):
        response = self.client.post(
            reverse("like_view", kwargs={"story_id": self.story.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        story = Story.objects.get(title="test")
        self.assertEqual(bool(self.user in story.like.all()), True)
        self.assertEqual(story.like_count, 1)
        self.assertEqual(response.data["like_count"], 1)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("like_view", kwargs={"story_id": self.story.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        story = Story.objects.get(title="test")
        self.assertEqual(bool(self.user in story.like.all()), False)
        self.assertEqual(story.like_count, 0)
        self.assertEqual(response.data["like_count"], 0)
        self.assertEqual(response.status_code, 200)

    def hate_story_test(self):
        response = self.client.post(
            reverse("hate_view", kwargs={"story_id": self.story.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        story = Story.objects.get(title="test")
        self.assertEqual(bool(self.user in story.hate.all()), True)
        self.assertEqual(story.hate_count, 1)
        self.assertEqual(response.data["hate_count"], 1)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("hate_view", kwargs={"story_id": self.story.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        story = Story.objects.get(title="test")
        self.assertEqual(bool(self.user in story.hate.all()), False)
        self.assertEqual(story.hate_count, 0)
        self.assertEqual(response.data["hate_count"], 0)
        self.assertEqual(response.status_code, 200)

    def bookmark_story_test(self):
        response = self.client.post(
            reverse("bookmark_view", kwargs={"story_id": self.story.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        story = Story.objects.get(title="test")
        self.assertEqual(bool(self.user in story.bookmark.all()), True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("bookmark_view", kwargs={"story_id": self.story.id}),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        story = Story.objects.get(title="test")
        self.assertEqual(bool(self.user in story.bookmark.all()), False)
        self.assertEqual(response.status_code, 200)
