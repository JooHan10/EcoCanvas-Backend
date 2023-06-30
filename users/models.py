from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
import re


def password_validator(password):
    '''
    작성자 : 이주한
    내용 : 비밀번호 유효성 검증 함수
    최초 작성일 : 2023.06.06
    업데이트 일자 :
    '''
    password_regex = '^(?=.*[\d])(?=.*[A-Z])(?=.*[a-z])(?=.*[!@#$%^&*()])[\w\d!@#$%^&*()]{8,}$'

    if not re.search(password_regex, str(password)):
        return True
    return False


def password_pattern(password):
    '''
    작성자 : 이주한
    내용 : 비밀번호 패턴 유효성 검증 함수
    최초 작성일 : 2023.06.06
    업데이트 일자 :
    '''
    password_pattern = r"(.)\1+\1"

    if re.search(password_pattern, str(password)):
        return True
    return False


class UserManager(BaseUserManager):
    '''
    작성자 : 이주한
    내용 : UserManager 모델
    최초 작성일 : 2023.06.06
    업데이트 일자 :
    '''

    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("이메일을 입력해주세요!")
        if not username:
            raise ValueError("이름을 입력해주세요!")

        user = self.model(
            email=self.normalize_email(email),
            username=username
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
        )

        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    '''
    작성자 : 이주한
    내용 : 
            2023.06.06: User 모델 생성
            2023.06.09: User 모델에 추가로 필요한 필드 추가(사용자 생성일, 정보 수정일, 탈퇴일)
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.19
    '''
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    username = models.CharField(verbose_name="user name", max_length=30,)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    withdrawal = models.BooleanField(default=False)
    withdrawal_at = models.DateTimeField(null=True, blank=True)
    login_type = models.CharField(max_length=10, default="normal")
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class UserProfile(models.Model):
    '''
    작성자: 장소은
    내용: 추가적인 사용자 정보를 저장해서 마이페이지나 주문 시 사용
    작성일: 2023.06.17
    '''
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True
    )
    address = models.CharField(max_length=255,  null=True)
    zip_code = models.CharField(max_length=10,  null=True)
    detail_address = models.CharField(max_length=255, null=True)
    delivery_message = models.TextField(blank=True, null=True)
    receiver_number = models.CharField(max_length=20, null=True)

    def __str__(self):
        return self.user.email

