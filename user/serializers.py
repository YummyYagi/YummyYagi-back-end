from rest_framework import serializers, exceptions
from user.models import User, Claim
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# 회원가입
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'country', 'nickname', 'profile_img']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# 로그인
class LoginSerializer(TokenObtainPairSerializer):
    
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
    

class QnaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = ['content',]