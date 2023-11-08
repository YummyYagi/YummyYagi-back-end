from rest_framework import serializers
from story.models import Story, Content


class ContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Content
        fields = '__all__'


class StoryListSerializer(serializers.ModelSerializer):
    story_id = serializers.CharField(source='id')
    author_id = serializers.CharField(source='author')
    author_nickname = serializers.CharField(source='author.nickname')
    story_title = serializers.CharField(source='title')
    content = serializers.SerializerMethodField(method_name='get_first_content')

    def get_first_content(self, obj):
        first_content = obj.contents.first()
        if first_content:
            return {
                'story_first_paragraph': first_content.paragraph,
                'story_image': first_content.image.url,
            }

    class Meta:
        model = Story
        fields = ('story_id', 'author_id', 'author_nickname', 'story_title', 'content')