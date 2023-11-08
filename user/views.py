from rest_framework.views import APIView
from rest_framework.response import Response
from story.models import Story
from user.models import User
from rest_framework import status, permissions
from user.serializers import UserSerializer, LoginSerializer, UserInfoSerializer, QnaSerializer, MypageSerializer, PasswordSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.generics import get_object_or_404
from user.models import User
from user.permissions import IsAuthenticatedOrIsOwner
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
import random
import string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from .tasks import send_verification_email

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
        if check_password(request.data['password'], user.password) == True:
            serializer = UserInfoSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status':'200', 'user_info':serializer.data}, status = status.HTTP_200_OK)
            else:
                return Response({'status':'400', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status':'403', 'error':'비밀번호가 일치하지 않습니다.'}, status=status.HTTP_403_FORBIDDEN)

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

        if request.data:
            password = request.data.get("password", "")
            auth_user = authenticate(email=request.user.email, password=password)
            if auth_user:
                auth_user.delete()
                return Response({'status': '204', 'error': '회원 탈퇴가 완료되었습니다.'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'status': '401', 'error': '비밀번호가 불일치합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'status': '400', 'error': '비밀번호를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)


class QnaView(APIView):
    permission_classes = [IsAuthenticatedOrIsOwner]
    
    """Q&A를 작성합니다."""
    def post(self, request):
        serializer = QnaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response({'status':'201', 'success':'등록되었습니다.'}, status=status.HTTP_201_CREATED)
        elif 'content' in serializer.errors:
            return Response({'status':'400', 'error':'내용을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)      
        else:
            return Response({'status':'400', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """비밀번호 찾기 기능입니다."""
    def post(self, request):
        
        try:
            user = User.objects.get(email = request.data['email'])
        except User.DoesNotExist:
            return Response({'status':'400', 'error':'입력하신 이메일을 찾을 수 없습니다.'})
        
        # 랜덤 비밀번호 생성
        temp_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
        
        user.set_password(temp_password)
        user.save()
        
        subject = '임시 비밀번호 발급'
        message = f'임시 비밀번호: {temp_password}'
        from_email = 'yammyyagi@gmail.com'
        recipient_list = [request.data['email']]
        send_mail(subject, message, from_email, recipient_list)
        
        return Response({'status': '200', 'success': '임시 비밀번호가 이메일로 전송되었습니다.'}, status=status.HTTP_200_OK)