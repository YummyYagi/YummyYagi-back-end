from rest_framework.views import APIView


class RegisterView(APIView):
    """사용자 정보를 받아 회원가입 합니다."""
    def post(self, request):
        pass


class EmailCheckView(APIView):
    """이메일 중복 검사를 위한 클래스 뷰입니다."""
    def post(self, request):
        pass


class NicknameCheckView(APIView):
    """닉네임 중복 검사를 위한 클래스 뷰입니다."""
    def post(self, request):
        pass


class LoginView(APIView):
    """
    사용자 정보를 받아 로그인 합니다.
    
    DRF의 JWT 토큰 인증 로그인 방식에 기본 제공되는 클래스 뷰를 상속받아 재정의합니다.
    """
    pass


class MyPageView(APIView):
    """사용자의 마이페이지입니다."""
    def get(self, request):
        pass


class UserInfoView(APIView):
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
        pass

    
class QnaView(APIView):
    def get(self, request):
        """Q&A 페이지입니다."""
        pass
    
    def post(self, request):
        """Q&A를 작성합니다."""
        pass