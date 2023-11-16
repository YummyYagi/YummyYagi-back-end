from rest_framework import serializers
from story.models import Story, Content, Comment
from user.models import User

class StoryCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        fields = ['title',]

class ContentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Content
        fields = ['paragraph', 'image']

class ContentSerializer(serializers.ModelSerializer):
    content_id = serializers.CharField(source='id')
    story_image = serializers.ImageField(source='image')
    story_id = serializers.CharField(source='story.id')

    
    class Meta:
        model = Content
        fields = ['story_id', 'content_id', 'paragraph', 'story_image']

class UserIdSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id',]

class StorySerializer(serializers.ModelSerializer):
    story_id = serializers.CharField(source='id')
    author_id = serializers.CharField(source='author.id')
    author_nickname = serializers.CharField(source='author.nickname')
    story_title = serializers.CharField(source='title')
    story_paragraph_list = ContentSerializer(source='contents', many=True)
    bookmark_user_list = serializers.SerializerMethodField()

    def get_bookmark_user_list(self, story):
        users = story.bookmark.all()
        user_data = UserIdSerializer(users, many=True).data
        return user_data
    
    class Meta:
        model = Story
        fields = ['story_id', 'author_id', 'author_nickname', 'story_title', 'story_paragraph_list', 'bookmark_user_list', 'like_count', 'hate_count']


class StoryListSerializer(serializers.ModelSerializer):
    story_id = serializers.CharField(source='id')
    author_id = serializers.CharField(source='author')
    author_nickname = serializers.CharField(source='author.nickname')
    author_country = serializers.CharField(source='author.country')
    story_title = serializers.CharField(source='title')
    content = serializers.SerializerMethodField(method_name='get_first_content')
    like_user_list = serializers.SerializerMethodField()
    
    def get_like_user_list(self, story):
            users = story.like.all()
            user_data = UserIdSerializer(users, many=True).data
            return user_data
        
    def get_first_content(self, obj):
        first_content = obj.contents.first()
        if first_content:
            return {
                'story_first_paragraph': first_content.paragraph,
                'story_image': first_content.image.url,
            }

    class Meta:
        model = Story
        fields = ['story_id', 'author_id', 'author_nickname', 'story_title', 'content', 'author_country', 'like_user_list']


class CommentSerializer(serializers.ModelSerializer):
    comment_id = serializers.CharField(source='id')
    author_id = serializers.CharField(source='author')
    author_nickname = serializers.CharField(source='author.nickname')
    author_image = serializers.ImageField(source='author.profile_img')
    
    class Meta:
        model = Comment
        fields = ['comment_id', 'author_id', 'author_nickname', 'story_id', 'content', 'author_image']
       
        
    def get_nickname(self, obj):
        return obj.author.nickname
    

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']