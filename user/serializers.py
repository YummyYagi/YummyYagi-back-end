from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re

from user.models import User, Claim
from story.serializers import StoryListSerializer
from story.models import Story

class UserSerializer(serializers.ModelSerializer):
    """회원가입을 위한 시리얼라이저입니다."""
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'country', 'nickname', 'profile_img']

    def validate(self, data):
        password = data.get('password')
        pattern = r'^(?=.*?[0-9])(?=.*?[#?!@$~%^&*-]).{8,20}$'
        if not re.match(pattern, password):
            raise exceptions.ValidationError({'password':'비밀번호는 8자 이상 20자 이하 및 숫자와 특수 문자(#?!@$~%^&*-)를 하나씩 포함시켜야 합니다.'})
        return data
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """로그인을 위한 시리얼라이저입니다."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, request_data):
        request_email = request_data.get('email')
        request_password = request_data.get('password')

        try:
            user = User.objects.get(email=request_email)
        except User.DoesNotExist:
            raise exceptions.NotFound({'status':'404', 'error':'사용자를 찾을 수 없습니다. 로그인 정보를 확인하세요.'})
        
        if not user.check_password(request_password):
            raise exceptions.AuthenticationFailed({'status':'401', 'error':'비밀번호가 일치하지 않습니다.'})
        elif user.is_active == False:
            raise exceptions.AuthenticationFailed({'status':'403', 'error':'이메일 인증이 필요합니다.'})
        else:
            data = super().validate(request_data)
            return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['nickname'] = user.nickname
        token['profile_img'] = user.profile_img.url

        return token


class MypageSerializer(serializers.ModelSerializer):
    my_story_list = serializers.SerializerMethodField(method_name='get_my_story_list')
    bookmark_story_list = serializers.SerializerMethodField(method_name='get_bookmark_story_list')
    story_timestamps = serializers.SerializerMethodField(method_name='get_story_timestamps')
    
    def get_my_story_list(self, obj):
        my_stories = obj.story_set.filter(hate_count__lte=4).order_by('-created_at')
        return StoryListSerializer(my_stories, many=True).data

    def get_bookmark_story_list(self, obj):
        bookmarked_stories = obj.bookmark_stories.filter(hate_count__lte=4).order_by('-created_at')
        return StoryListSerializer(bookmarked_stories, many=True).data

    def get_story_timestamps(self, obj):
        stories=Story.objects.all().filter(hate_count__lte=4, timestamps__user=obj).order_by('-timestamps__timestamp')
        return StoryListSerializer(stories,many=True).data
    

    class Meta:
        model = User
        fields = ['email', 'nickname', 'profile_img', 'country', 'bookmark_story_list', 'my_story_list', 'story_timestamps']


class UserInfoSerializer(serializers.ModelSerializer):
    """회원정보 수정을 위한 시리얼라이저입니다."""

    class Meta:
        model = User
        fields = ['country', 'nickname', 'profile_img']

    def update(self, instance, validated_data):
        
        user = super().update(instance, validated_data)
        user.save()
        return user

class PasswordSerializer(serializers.ModelSerializer):
    """사용자의 비밀번호 변경을 위한 시리얼라이저입니다."""

    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_check = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ['current_password', 'new_password', 'new_password_check']

    def validate(self, data):
        password = data.get('new_password')
        pattern = r'^(?=.*?[0-9])(?=.*?[#?!@$~%^&*-]).{8,20}$'
        if not re.match(pattern, password):
            raise exceptions.ValidationError({'password':'비밀번호는 8자 이상 20자 이하 및 숫자와 특수 문자(#?!@$~%^&*-)를 하나씩 포함시켜야 합니다.'})
        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('new_password')
        instance.set_password(password)
        user = super().update(instance, validated_data)
        user.save()
        return user

class QnaSerializer(serializers.ModelSerializer):
    """Q&A 피드백을 위한 시리얼라이저입니다."""

    class Meta:
        model = Claim
        fields = ['content',]
