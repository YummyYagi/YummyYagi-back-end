from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from user.models import User
from user.serializers import UserSerializer, LoginSerializer, QnaSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
# 이메일인증 import
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
        pass


class UserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        """사용자의 회원 정보 수정 페이지입니다."""
        pass
    
    def put(self, request):
        """사용자의 정보를 받아 회원 정보를 수정합니다."""
        pass
    
    def patch(self, request):
        """사용자의 정보를 받아 비밀번호를 수정합니다."""
        pass
    
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
    def post(self, request):
        """Q&A를 작성합니다."""
        serializer = QnaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response({'status':'201', 'success':'등록되었습니다.'}, status=status.HTTP_201_CREATED)
        elif 'content' in serializer.errors:
            return Response({'status':'400', 'error':'내용을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)      
        else:
            return Response({'status':'400', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)