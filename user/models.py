from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from story.models import Story

class UserManager(BaseUserManager):

    """ 사용자 모델을 생성하고 관리하는 클래스입니다. """

    def create_user(self, email, nickname, country, password):
        """ 일반 사용자를 생성하는 메서드입니다. """
        
        if not email:
            raise ValueError('유효하지 않은 이메일 형식입니다.')
        
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
        """ 관리자를 생성하는 메서드입니다. """
        
        if not email:
            raise ValueError('유효하지 않은 이메일 형식입니다.')
        
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
    
    ('대한민국', '대한민국'),
    ('미국', '미국'),
    ('프랑스', '프랑스'),
    ('스페인', '스페인'),
    ('일본', '일본'),
    ('중국', '중국')
]

class User(AbstractBaseUser) :
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

    email = models.EmailField('이메일', max_length=255, unique=True)
    password = models.CharField('비밀번호', max_length=500)
    nickname = models.CharField('활동 아이디', max_length=30, unique=True)
    country = models.CharField('국가', choices=COUNTRY_CHOICES, max_length=50)
    profile_img = models.ImageField('프로필 이미지', upload_to='user/%Y/%m/', blank=True, default="user/default_profile.jpg")
    is_admin = models.BooleanField('관리자 여부', default=False)
    is_active = models.BooleanField('계정 활성화 여부', default=False)
    recent_stories = models.ManyToManyField(Story, through='RecentStory')


    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname', 'country']

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
        db_table = 'user'
        
        
class RecentStory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  
        

class Claim(models.Model):
    """
    - author : Q&A 작성자입니다.
        - 로그인 한 사용자를 자동으로 지정합니다.
    - content : Q&A 내용입니다.
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="작성자", on_delete=models.CASCADE)
    content = models.TextField()
    
    class Meta:
        db_table = 'claim'