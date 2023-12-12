from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from story.models import Story


class UserManager(BaseUserManager):

    """사용자 모델을 생성하고 관리하는 클래스입니다."""

    def create_user(self, email, nickname, country, password):
        """일반 사용자를 생성하는 메서드입니다."""

        if not email:
            raise ValueError("유효하지 않은 이메일 형식입니다.")

        user = self.model(
            email=self.normalize_email(email),
            password=password,
            nickname=nickname,
            country=country,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nickname, country, password=None):
        """관리자를 생성하는 메서드입니다."""

        if not email:
            raise ValueError("유효하지 않은 이메일 형식입니다.")

        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            nickname=nickname,
            country=country,
        )

        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)
        return user


COUNTRY_CHOICES = [
    # 관리자 페이지에서 사용자의 출신 국가 Dropdown 선택 기능을 사용하기 위해 추가한 옵션입니다.
    ("대한민국", "대한민국"),
    ("미국", "미국"),
    ("프랑스", "프랑스"),
    ("스페인", "스페인"),
    ("일본", "일본"),
    ("중국", "중국"),
    ("", ""),
]


class User(AbstractBaseUser):
    """
    사용자 모델을 정의하는 클래스입니다.

    - email(필수) : 로그인 시 사용할 사용자의 이메일 주소입니다.
        - 다른 사용자의 이메일과 중복되지 않도록 설정합니다. (Unique)
    - password(필수) : 사용자의 비밀번호입니다.
    - nickname(필수) : 사용자의 활동 아이디입니다.
        - 다른 사용자의 닉네임과 중복되지 않도록 설정합니다. (Unique)
    - country(필수) : 사용자의 출신 국가입니다.
    - profile_img : 사용자의 프로필 이미지입니다.
        - 프로필 이미지를 등록하지 않을 경우, default 이미지 url을 저장합니다.
    - is_admin : 관리자 권한 여부입니다.
        - True 혹은 False를 저장할 수 있으며, 기본값으로 False를 저장하도록 설정합니다.
    - is_active : 계정 활성화 여부입니다.
        - True 혹은 False를 저장할 수 있으며, 기본값으로 False를 저장하도록 설정합니다.
    """

    email = models.EmailField("이메일", max_length=255, unique=True)
    password = models.CharField("비밀번호", max_length=500)
    nickname = models.CharField("활동 아이디", max_length=30, unique=True)
    country = models.CharField("국가", choices=COUNTRY_CHOICES, max_length=50)
    profile_img = models.ImageField(
        "프로필 이미지",
        upload_to="user/%Y/%m/",
        blank=True,
        default="user/default_profile.jpg",
    )
    is_admin = models.BooleanField("관리자 여부", default=False)
    is_active = models.BooleanField("계정 활성화 여부", default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "country"]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    class Meta:
        db_table = "user"


class UserStoryTimeStamp(models.Model):
    """
    - user : 스토리를 조회한 유저입니다.
    - story : 사용자가 조회한 스토리입니다.
    - timestamp : 사용자가 스토리를 조회한 시간을 기록합니다.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="timestamps")
    story = models.ForeignKey(
        Story, on_delete=models.CASCADE, related_name="timestamps"
    )
    timestamp = models.DateTimeField("Time Stamp", auto_now=True, blank=True, null=True)


class Ticket(models.Model):
    """
    - member : 티켓을 구매한 유저입니다.
        - 티켓을 구매한 사용자를 자동으로 지정합니다.
    - golden_ticket : 1등급 티켓입니다.
        - DALL-E3 HD 엔진 API 요청을 통해 이미지를 생성합니다.
    - silver_ticket : 2등급 티켓입니다.
        - DALL-E3 Standard 엔진 API 요청을 통해 이미지를 생성합니다.
    - pink_ticket : 3등급 티켓입니다.
        - DALL-E2 엔진 API 요청을 통해 이미지를 생성합니다.
    """

    ticket_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="작성자",
        related_name="tickets",
        on_delete=models.CASCADE,
    )
    golden_ticket = models.PositiveIntegerField("골드 티켓", default=1)
    silver_ticket = models.PositiveIntegerField("실버 티켓", default=2)
    pink_ticket = models.PositiveIntegerField("핑크 티켓", default=10)

    class Meta:
        db_table = "ticket"


class PaymentResult(models.Model):
    """
    - buyer_email : 구매자의 이메일입니다.
    - buyer_nickname : 구매자의 아이디입니다.
    - name : 구매한 상품명입니다.
    - paid_amount : 결제 금액입니다.
    - currency : 화폐 단위
    - pg_provider : 결제 프로세서입니다.
    - pg_tic : 거래 식별자입니다. 결제 내역 조회, 환불 처리 등에 활용될 수 있습니다.
    - pay_method : 결제 방법입니다.
    - bank_name : 은행명입니다.
    - card_name : 카드명입니다.
    - card_number : 카드명입니다.
    - receipt_url : 영수증 url입니다.
    - status : 'ready', 'paid', 'canceled', 'failed' 등의 처리 상태입니다.
    """

    buyer_email = models.EmailField("구매자 이메일", max_length=255)
    buyer_name = models.CharField("구매자 아이디", max_length=30)
    name = models.CharField("구매 상품명", max_length=30)
    paid_amount = models.PositiveIntegerField("결제 금액")
    currency = models.CharField("통화", max_length=30, null=True, blank=True)
    pg_provider = models.CharField("결제 게이트웨이 제공자", max_length=30)
    pg_tid = models.TextField("결제 ID", null=True, blank=True)
    pay_method = models.CharField("결제 방법", max_length=30)
    bank_name = models.CharField("은행명", max_length=30, null=True, blank=True)
    card_name = models.CharField("카드명", max_length=30, null=True, blank=True)
    card_number = models.CharField("카드 번호", max_length=50, null=True, blank=True)
    receipt_url = models.URLField("영수증 url", null=True, blank=True)
    status = models.CharField("처리 상태", max_length=30)

    class Meta:
        db_table = "payment result"


class Claim(models.Model):
    """
    - author : Q&A 작성자입니다.
        - 로그인 한 사용자를 자동으로 지정합니다.
    - content : Q&A 내용입니다.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="작성자", on_delete=models.CASCADE
    )
    content = models.TextField()

    class Meta:
        db_table = "claim"
