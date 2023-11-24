from rest_framework import status
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.generics import get_object_or_404
from user.models import User
from user.permissions import IsAuthenticatedOrIsOwner
from user.serializers import UserSerializer, LoginSerializer, UserInfoSerializer, QnaSerializer, MypageSerializer, PasswordSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
import random
import string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from .tasks import send_verification_email, send_verification_email_for_pw, send_email_with_pw
import requests
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterView(APIView):
    """사용자 정보를 받아 회원가입 합니다."""

    def post(self, request):
        if request.data['password'] != request.data['password_check']:
            return Response({'status':'400', 'error':'비밀번호를 확인해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user=serializer.save()
                # 이메일 확인 토큰 생성
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                # 이메일에 인증 링크 포함하여 보내기
                verification_url = f'http://127.0.0.1:8000/user/verify-email/{uid}/{token}/'
                send_verification_email.delay(user.id, verification_url, user.email)
                
                return Response({'status':'201', 'success':'회원가입 성공'}, status=status.HTTP_201_CREATED)
            return Response({'status':'400', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """이메일 인증을 처리합니다."""
    def get(self, request, uidb64, token):
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(id=uid)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
        return Response(status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    """
    사용자 정보를 받아 로그인 합니다.
    
    DRF의 JWT 토큰 인증 로그인 방식에 기본 제공되는 클래스 뷰를 상속받아 재정의합니다.
    """
    serializer_class = LoginSerializer
    
    
BASE_URL = "http://127.0.0.1:5501/user/register.html"

class SocialUrlView(APIView):
    def post(self,request):
        social = request.data.get('social',None)
        if social is None:
            return Response({'error':'소셜로그인이 아닙니다'},status=status.HTTP_400_BAD_REQUEST)
        elif social == 'kakao':
            url = 'https://kauth.kakao.com/oauth/authorize?client_id=' + settings.KAKAO_REST_API_KEY + '&redirect_uri=' + BASE_URL + '&response_type=code&prompt=login'
            return Response({'url':url},status=status.HTTP_200_OK)
        

class KakaoLoginView(APIView):
    def post(self,request):
        code = request.data.get('code')
        access_token = requests.post("https://kauth.kakao.com/oauth/token",
            headers={"Content-Type":"application/x-www-form-urlencoded"},
            data={
                "grant_type":"authorization_code",
                "client_id": settings.KAKAO_REST_API_KEY,
                "redirect_uri":BASE_URL,
                "code":code,
                'client_secret': settings.KAKAO_SECRET_KEY,
            },
        )
        access_token = access_token.json().get("access_token")
        user_data_request = requests.get("https://kapi.kakao.com/v2/user/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
            },
        )
        user_datajson = user_data_request.json()
        user_data = user_datajson["kakao_account"]
        email = user_data["email"]
        nickname = user_data["profile"]["nickname"]
        

        try:
            user = User.objects.get(email=email)
            print("1:", user.is_active)
            user.is_active = True
            user.save()
            refresh = RefreshToken.for_user(user)
            refresh["email"] = user.email
            refresh["nickname"] = user.nickname
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK
            )
        except:
            user = User.objects.create_user(email=email,nickname=nickname)
            user.set_unusable_password()
            user.save()
            refresh = RefreshToken.for_user(user)
            refresh["email"] = user.email
            refresh["nickname"] = user.nickname
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    'status':'200',
                },
                status=status.HTTP_200_OK
            )


class MyPageView(APIView):
    """사용자의 마이페이지입니다."""

    def get(self, request):
        user = request.user
        serializer = MypageSerializer(user)
        return Response({'status':'200', 'my_data':serializer.data}, status=status.HTTP_200_OK)


class UserInfoView(APIView):
    permission_classes = [IsAuthenticatedOrIsOwner]
    
    def get(self, request):
        """사용자의 회원 정보 수정 페이지입니다."""

        user = get_object_or_404(User, id=request.user.id)
        serializer = UserInfoSerializer(user)
        return Response({'status':'200', 'user_info':serializer.data}, status = status.HTTP_200_OK)
    
    def put(self, request):
        """사용자의 정보를 받아 회원 정보를 수정합니다."""

        user = get_object_or_404(User, id=request.user.id)
        serializer = UserInfoSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':'200', 'success':'회원 정보가 수정되었습니다.'}, status = status.HTTP_200_OK)
        else:
            return Response({'status':'400', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request):
        """사용자의 정보를 받아 비밀번호를 수정합니다."""

        user = get_object_or_404(User, id=request.user.id)
        if not request.data['current_password'] or not request.data['new_password'] or not request.data['new_password_check']:
            return Response({'status':'400', 'error':'모든 필수 정보를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        elif check_password(request.data['current_password'], user.password) == False:
            return Response({'status':'400', 'error':'현재 비밀번호가 일치하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        elif request.data['current_password'] == request.data['new_password']:
            return Response({'status':'400', 'error':'비밀번호 변경에는 현재 비밀번호와 다른 비밀번호를 사용해야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        elif request.data['new_password'] != request.data['new_password_check']:
            return Response({'status':'400', 'error':'새 비밀번호가 새 비밀번호 확인과 일치하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = PasswordSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':'200', 'success':'비밀번호 수정 완료'}, status = status.HTTP_200_OK)
            return Response({'status':'400', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request):
        """사용자의 회원 탈퇴 기능입니다."""

        password = request.data.get('password', '')
        if not password:
            return Response({'status': '400', 'error': '비밀번호를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
        auth_user = authenticate(email=request.user.email, password=password)
        if auth_user:
            auth_user.delete()
            return Response({'status': '204', 'success': '회원 탈퇴가 완료되었습니다.'})
        else:
            return Response({'status': '401', 'error': '비밀번호가 불일치합니다.'}, status=status.HTTP_401_UNAUTHORIZED)


class QnaView(APIView):
    permission_classes = [IsAuthenticatedOrIsOwner]
    
    """Q&A를 작성합니다."""
    def post(self, request):
        serializer = QnaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response({'status':'201', 'success':'건의 작성 완료'}, status=status.HTTP_201_CREATED)
        elif 'content' in serializer.errors:
            return Response({'status':'400', 'error':'내용을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)      
        else:
            return Response({'status':'400', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """랜덤 비밀번호 발급을 위한 인증 이메일을 보내는 뷰입니다."""
    def post(self, request):
        
        try:
            user = User.objects.get(email = request.data['email'])
        except User.DoesNotExist:
            return Response({'status':'400', 'error':'입력하신 이메일을 찾을 수 없습니다.'})
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # 이메일에 인증 링크 포함하여 보내기
        verification_url = f'http://127.0.0.1:8000/user/verify-email-for-pw/{uid}/{token}/'
        send_verification_email_for_pw.delay(user.id, verification_url, user.email)
        
        return Response({'status': '200', 'success': '임시 비밀번호 발급을 위한 인증 이메일이 전송되었습니다.'}, status=status.HTTP_200_OK)
    
class SendRandomPassword(APIView):
    """인증 이메일 클릭 시 랜덤 비밀번호를 발급하는 뷰입니다."""
    def get(self, request, uidb64, token):
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(id=uid)

        if default_token_generator.check_token(user, token):
            temp_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    
            user.set_password(temp_password)
            user.save()
            
            send_email_with_pw.delay(user.id, temp_password, user.email)
            
        return Response({'status': '200', 'success': '임시 비밀번호가 이메일로 발송되었습니다.'}, status=status.HTTP_200_OK)