from rest_framework import serializers
from story.models import Story, Content, Comment


class ContentSerializer(serializers.ModelSerializer):
    content_id = serializers.CharField(source='id')
    story_image = serializers.CharField(source='image')
    story_id = serializers.CharField(source='story.id')
    
    class Meta:
        model = Content
        fields = ['story_id', 'content_id', 'paragraph', 'story_image']


class StorySerializer(serializers.ModelSerializer):
    story_id = serializers.CharField(source='id')
    author_id = serializers.CharField(source='author')
    author_nickname = serializers.CharField(source='author.nickname')
    story_title = serializers.CharField(source='title')
    story_paragraph_list = ContentSerializer(source='contents', many=True)

    class Meta:
        model = Story
        fields = ['story_id', 'author_id', 'author_nickname', 'story_title', 'story_paragraph_list']


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
        fields = ['story_id', 'author_id', 'author_nickname', 'story_title', 'content']
        

class CommentSerializer(serializers.ModelSerializer):
    comment_id = serializers.CharField(source='id')
    author_id = serializers.CharField(source='author')
    author_nickname = serializers.CharField(source='author.nickname')
    
    class Meta:
        model = Comment
        fields = ['comment_id', 'author_id', 'author_nickname', 'story_id', 'content']
       
        
    def get_nickname(self, obj):
        return obj.author.nickname
    

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']