import uuid
import random
import string
import requests
from datetime import datetime
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.db.models import Sum
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import get_object_or_404
from user.models import User, Ticket, PaymentResult as PaymentResultModel
from user.permissions import IsAuthenticatedOrIsOwner, IsAuthenticated
from user.serializers import UserSerializer, LoginSerializer, UserInfoSerializer, QnaSerializer, MypageSerializer, PasswordSerializer, PaymentResultSerializer
from .tasks import send_verification_email, send_verification_email_for_pw, send_email_with_pw
import requests
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
import secrets



class RegisterView(APIView):
    """사용자 정보를 받아 회원가입 합니다."""

    def post(self, request):
        if request.data['password'] != request.data['password_check']:
            return Response({'status':'400', 'error':'비밀번호를 확인해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user=serializer.save()

                # 회원가입 시 기본 티켓 제공
                Ticket.objects.create(ticket_owner=user)

                # 이메일 확인 토큰 생성
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # 이메일에 인증 링크 포함하여 보내기
                verification_url = f'https://api.yummyyagi.com/user/verify-email/{uid}/{token}/'
                
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
        url = "https://www.yummyyagi.com/user/login.html"
        return redirect(url)


class LoginView(TokenObtainPairView):
    """
    사용자 정보를 받아 로그인 합니다.
    
    DRF의 JWT 토큰 인증 로그인 방식에 기본 제공되는 클래스 뷰를 상속받아 재정의합니다.
    """
    serializer_class = LoginSerializer


BASE_URL = "http://127.0.0.1:5501/"
STATE = secrets.token_urlsafe(16)


class SocialUrlView(APIView):
    def post(self,request):
        social = request.data.get('social',None)
        if social is None:
            return Response({'error':'소셜로그인이 아닙니다'},status=status.HTTP_400_BAD_REQUEST)
        elif social == 'kakao':
            url = 'https://kauth.kakao.com/oauth/authorize?client_id=' + settings.KAKAO_REST_API_KEY + '&redirect_uri=' + BASE_URL + '&response_type=code&prompt=login'
            return Response({'url':url},status=status.HTTP_200_OK)
        elif social == 'google':
            client_id = settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID
            redirect_uri = BASE_URL 
            url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=email%20profile"
            return Response({'url': url}, status=status.HTTP_200_OK)
        elif social == 'naver':
            url = "https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id="+ settings.SOCIAL_AUTH_NAVER_CLIENT_ID + "&redirect_uri=" + BASE_URL + "&state=" + STATE
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

        if access_token.status_code != 200:
            return Response({"status":"400", "error": "카카오 로그인 실패. 다시 시도해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
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

        data = {
            "email" : email,
            "password" : "aaaa1111~",
            "nickname" : nickname,
            "country" : ""
        }

        try:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            refresh["email"] = user.email
            refresh["nickname"] = user.nickname
            refresh['profile_img'] = user.profile_img.url
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK
            )
        except:
            serializer = UserSerializer(data = data)

            if serializer.is_valid():
                serializer.save()
                user = User.objects.get(email=email)
                user.is_active = True
                user.set_unusable_password()
                user.save()
                Ticket.objects.create(ticket_owner=user)
                refresh = RefreshToken.for_user(user)
                refresh["email"] = user.email
                refresh["nickname"] = user.nickname
                refresh['profile_img'] = user.profile_img.url
                return Response(
                    {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    status=status.HTTP_200_OK
            )


class NaverLoginView(APIView):
    def post(self, request):
        code = request.data.get('code')
        client_id = settings.SOCIAL_AUTH_NAVER_CLIENT_ID
        client_secret = settings.SOCIAL_AUTH_NAVER_SECRET
        redirect_uri = BASE_URL
        
        # 네이버 API로 액세스 토큰 요청
        access_token_request = requests.post("https://nid.naver.com/oauth2.0/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        
        if access_token_request.status_code != 200:
            return Response({"status":"400", "error": "네이버 로그인 실패. 다시 시도해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        access_token_json = access_token_request.json()
        access_token = access_token_json.get("access_token")

        # 네이버 API로 사용자 정보 요청
        user_data_request = requests.get("https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    },
        )

        user_data_json = user_data_request.json()
        user_data = user_data_json.get("response")

        email = user_data.get("email")
        nickname = user_data.get("nickname")

        data = {
            "email" : email,
            "password" : "aaaa1111~",
            "nickname" : nickname,
            "country" : ""
        }

        try:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            refresh["email"] = user.email
            refresh["nickname"] = user.nickname
            refresh['profile_img'] = user.profile_img.url
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK
            )
        except:
            serializer = UserSerializer(data = data)

            if serializer.is_valid():
                serializer.save()
                user = User.objects.get(email=email)
                user.is_active = True
                user.set_unusable_password()
                user.save()
                Ticket.objects.create(ticket_owner=user)
                refresh = RefreshToken.for_user(user)
                refresh["email"] = user.email
                refresh["nickname"] = user.nickname
                refresh['profile_img'] = user.profile_img.url
                return Response(
                    {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    status=status.HTTP_200_OK
            )


class GoogleLoginView(APIView):
    def post(self, request):
        code = request.data.get('code')

        client_id = settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID
        client_secret = settings.SOCIAL_AUTH_GOOGLE_CLIENT_SECRET
        redirect_uri = BASE_URL

        #  구글 API로 액세스 토큰 요청
        access_token_request = requests.post("https://oauth2.googleapis.com/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "scope": "email profile",
            }
        )

        if access_token_request.status_code != 200:
            return Response({"status":"400", "error": "구글 로그인 실패. 다시 시도해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        access_token_json = access_token_request.json()
        access_token = access_token_json.get("access_token")
        
        # 구글 API로 사용자 정보 요청
        user_data_request = requests.get("https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data_json = user_data_request.json()

        email = user_data_json.get("email")
        nickname = user_data_json.get("name")

        data = {
            "email" : email,
            "password" : "aaaa1111~",
            "nickname" : nickname,
            "country" : ""
        }
        try:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            refresh["email"] = user.email
            refresh["nickname"] = user.nickname
            refresh['profile_img'] = user.profile_img.url
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK
            )
        except:
            serializer = UserSerializer(data = data)

            if serializer.is_valid():
                serializer.save()
                user = User.objects.get(email=email)
                user.is_active = True
                user.set_unusable_password()
                user.save()
                Ticket.objects.create(ticket_owner=user)
                refresh = RefreshToken.for_user(user)
                refresh["email"] = user.email
                refresh["nickname"] = user.nickname
                refresh['profile_img'] = user.profile_img.url
                return Response(
                    {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
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
        verification_url = f'https://api.yummyyagi.com/user/verify-email-for-pw/{uid}/{token}/'
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


def load_payment(request, user) :
    """지금까지 사용자의 총 결제 금액과 현 요청 금액을 더한 값이 20000원 이하일 경우 실행되는 함수입니다."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = uuid.uuid4().hex[:6]  # 6자리의 무작위 문자열 생성
    merchant_uid = f"{timestamp}-{unique_id}"

    order_data = {
        'pg_cid' : settings.PG_CID,
        'merchant_uid' : merchant_uid,
        'amount' : request.data['amount'],
        'name' : request.data['name'],
        'buyer_email' : user.email,
        'buyer_name' : user.nickname, 
    }
    return Response({'status':'200', 'order_data':order_data}, status=status.HTTP_200_OK)

class PaymentPageView(APIView):
    """주문 정보 페이지를 로드하기 위한 뷰입니다."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = User.objects.get(id=request.user.id)

        # 사용자의 총 결제액 조회
        user_total_payment = PaymentResultModel.objects.filter(buyer_email=user.email).aggregate(Sum('paid_amount'))
        total_paid_amount = user_total_payment['paid_amount__sum'] or 0

        # 새로운 결제 금액
        new_payment_amount = int(request.data['amount'].split(' ')[0])

        # 사용자 테스트를 위한 결제 제한 로직

        if total_paid_amount + new_payment_amount >= 20000:
            return Response({'status': '400', 'error': '죄송합니다. 결제 제한 초과로 인해 더 이상 결제를 진행할 수 없습니다. 현재까지 결제한 금액은 사용자별로 총 20,000원까지 허용됩니다.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return load_payment(request, user)

class PaymentResult(APIView):
    """결제 정보를 저장하는 뷰입니다."""
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # 구매자 이메일과 현재 로그인한 사용자 이메일 비교
        if request.user.email == request.data['rsp']['buyer_email']:
            serializer = PaymentResultSerializer(data=request.data['rsp'])
            print(serializer)
            if serializer.is_valid():
                result = serializer.save()

                # 상품명에 'G'가 포함된 경우 (티켓 구매 / 상품명 : G0S0P0)
                if 'G' in result.name:
                    # 티켓 개수 추출
                    tickets = result.name.split('_')
                    golden_ticket_cnt = int(tickets[0].split('G')[1])
                    silver_ticket_cnt = int(tickets[1].split('S')[1])
                    pink_ticket_cnt = int(tickets[2].split('P')[1])

                    # 사용자의 티켓 정보 업데이트
                    user_tickets = Ticket.objects.get(ticket_owner = request.user)

                    if golden_ticket_cnt > 0 :
                        user_tickets.golden_ticket += golden_ticket_cnt
                    
                    if silver_ticket_cnt > 0 :
                        user_tickets.silver_ticket += silver_ticket_cnt
                    
                    if pink_ticket_cnt > 0 :
                        user_tickets.pink_ticket += pink_ticket_cnt
                    
                    user_tickets.save()
                    
                return Response({'status':'201', 'success':'결제 완료'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'status': '400', 'error': '유효하지 않은 데이터입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'status': '403', 'error': '인증된 사용자의 정보와 일치하지 않습니다.'}, status=status.HTTP_403_FORBIDDEN)