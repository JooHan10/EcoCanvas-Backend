from rest_framework import serializers
from .models import User, UserProfile, password_validator, password_pattern
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import serializers, exceptions
from django.core.mail import EmailMessage
from django.utils.encoding import force_str
from django.utils.encoding import smart_bytes
from django.utils import timezone
import threading
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
import hashlib

class EmailThread(threading.Thread):
    '''
    작성자 : 이주한
    내용 : 이메일 전송을 위해 'Thread'를 사용하는 'EmailThread'클래스입니다.
            run 메소드는 Tread의 start() 메소드로 Tread가 실행될 때 호출됩니다.

            * Tread를 사용하는 이유: 
                이메일 전송 작업을 백그라운드에서 비동기적으로 처리하고, 
                다른 작업과 동시에 진행할 수 있도록 하기 위함입니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 : 
    '''

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


class Util:
    '''
    작성자 : 이주한
    내용 : 이메일 전송 시 양식을 정의한 클래스입니다.
            양식은 EmailMessage의 양식을 따르며, EmailThread(email).start()를 통해
            이메일 전송 작업이 백그라운드에서 비동기적으로 처리됩니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 : 
    '''
    @staticmethod
    def send_email(message):
        email = EmailMessage(
            subject=message["email_subject"],
            body=message["email_body"],
            to=[message["to_email"]],
        )
        EmailThread(email).start()


class SignUpSerializer(serializers.ModelSerializer):
    '''
    작성자 : 이주한
    내용 : 회원가입에 필요한 Sign Up Serializer 클래스
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.10
    '''
    re_password = serializers.CharField(
        error_messages={
            "required": "비밀번호 확인은 필수 입력 사항입니다!",
            "blank": "비밀번호 확인은 필수 입력 사항입니다!",
        }
    )

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "re_password",
            "email",
        )
        extra_kwargs = {
            "email": {
                "error_messages": {
                    "required": "email은 필수 입력 사항입니다!",
                    "invalid": "email 형식이 맞지 않습니다. 알맞은 형식의 email을 입력해주세요!",
                    "blank": "email은 필수 입력 사항입니다!",
                }
            },
            "username": {
                "error_messages": {
                    "required": "이름은 필수 입력 사항입니다!",
                    "blank": "이름은 필수 입력 사항입니다!",
                }
            },
            "password": {
                "write_only": True,
                "error_messages": {
                    "required": "비밀번호는 필수 입력 사항입니다!",
                    "blank": "비밀번호는 필수 입력 사항입니다!",
                },
            },
        }

    def validate(self, data):
        password = data.get("password")
        re_password = data.get("re_password")

        if password != re_password:
            raise serializers.ValidationError(
                detail={"password": "비밀번호와 비밀번호 확인이 일치하지 않습니다!"})

        if password_validator(password):
            raise serializers.ValidationError(
                detail={"password": "비밀번호는 8자 이상의 영문 대소문자와 숫자, 특수문자를 포함하여야 합니다!"})

        if password_pattern(password):
            raise serializers.ValidationError(
                detail={"password": "비밀번호는 연속해서 3자리 이상 동일한 영문,숫자,특수문자 사용이 불가합니다!"})

        return data

    def create(self, validated_data):
        email = validated_data["email"]
        username = validated_data["username"]
        password = validated_data["password"]
        validated_data.pop("re_password", None)
        user = User.objects.create(username=username, email=email,)
        user.set_password(password)
        user.save()

        return validated_data


class VerificationCodeGenerator:
    '''
        작성자 : 이주한
        내용 : 회원가입시 이메일 인증에 필요한 인증 코드를 생성하는 함수입니다.

        최초 작성일 : 2023.06.15
        업데이트 일자 : 2023.06.25
        '''
    @staticmethod
    def verification_code(email, time_check):
        ingredient = email + str(time_check)
        hashed_code = hashlib.sha256(ingredient.encode()).hexdigest()
        return hashed_code


class SendSignupEmailSerializer(serializers.Serializer):
    '''
    작성자 : 이주한
    내용 : SendSignupEmailView API가 호출될 때 사용되는 시리얼라이저입니다.
            사용자가 입력한 이메일이 존재하는 이메일인지 확인 후 존재할 경우
            에러 메시지를 띄워주고, 존재하지 않다면 로직을 계속합니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 : 
    '''
    email = serializers.EmailField(
        error_messages={
            "required": "이메일을 입력해주세요.",
            "blank": "이메일을 입력해주세요.",
        }
    )
    time_check = serializers.IntegerField()
    
    class Meta:
        fields = ("email", "date")

    def validate(self, attrs):
        email = attrs.get("email")
        time_check = attrs.get("time_check")
        verification_code = VerificationCodeGenerator.verification_code(email, time_check)
        
        try:
            User.objects.get(email=email)
            
            raise serializers.ValidationError(
                detail={"email": "이미 존재하는 계정의 이메일 주소입니다."})

        except User.DoesNotExist:
            email_body = "아래 인증코드를 인증코드 작성란에 기입해주세요. \n " + verification_code
            message = {
                "email_body": email_body,
                "to_email": email,
                "email_subject": "EcoCanvas 이메일 인증 코드",
            }
            Util.send_email(message)

            return super().validate(attrs)


class UserUpdateSerializer(serializers.ModelSerializer):
    '''
    작성자 : 이주한
    내용 : 회원정보 수정에 필요한 UserUpdateSerializer 클래스 입니다.
    최초 작성일 : 2023.06.14
    업데이트 일자 :
    '''
    class Meta:
        model = User
        fields = (
            "email",
        )
        extra_kwargs = {
            "email": {
                "error_messages": {
                    "required": "이메일을 입력해주세요.",
                    "blank": "이메일을 입력해주세요.",
                }
            },
        }

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.save()

        return instance


class UserWithdrawalSerializer(serializers.ModelSerializer):
    '''
    작성자 : 이주한
    내용 : 회원탈퇴에 필요한 UserWithdrawalSerializer 클래스 입니다.
    최초 작성일 : 2023.06.23
    업데이트 일자 :
    '''

    confirm_password = serializers.CharField(
        error_messages={
            "required": "비밀번호를 입력해주세요.",
            "blank": "비밀번호를 입력해주세요.",
        }
    )

    class Meta:
        model = User
        fields = (
            "confirm_password",
        )
        extra_kwargs = {
            "confirm_password": {
                "error_messages": {
                    "required": "비밀번호를 입력해주세요.",
                    "blank": "비밀번호를 입력해주세요.",
                },
            },
        }

    def validate(self, data):
        current_password = self.context.get("request").user.password
        confirm_password = data.get("confirm_password")

        if not check_password(confirm_password, current_password):
            raise serializers.ValidationError(
                detail={"confirm_password": "현재 비밀번호가 일치하지 않습니다."})

        return data

    def update(self, instance, validated_data):
        instance.is_active = False
        instance.withdrawal = True
        instance.withdrawal_at = timezone.now()
        instance.save()

        return instance


class UpdatePasswordSerializer(serializers.ModelSerializer):
    '''
    작성자 : 이주한
    내용 : 사용자가 로그인한 상태에서 본인 계정의 비밀번호를 수정할 때 사용되는 UpdatePasswordSerializer 입니다.
            로직에는 사용자가 비밀번호를 변경하기 위해 진행해야하는 예외처리 & 유효성 검사들이 있습니다.
            1. 현재 비밀번호를 입력하여 본인임을 인증하는 검사
            2. 현재 비밀번호와 바꿀 비밀번호 끼리의 중복 검사
            3. 비밀번호와 비밀번호 확인 일치 검사
            4. 비밀번호 유효성 검사
            5. 비밀번호의 문자들 중 3자리 이상 동일 문자 유/무 검사
            위의 유효성 검사들 중 4번과 5번은 개발 단계에서 번거로울 수 있으므로 주석 처리해 두었습니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 : 
    '''
    confirm_password = serializers.CharField(
        error_messages={
            "required": "비밀번호를 입력해주세요.",
            "blank": "비밀번호를 입력해주세요.",
        }
    )
    re_password = serializers.CharField(
        error_messages={
            "required": "비밀번호를 입력해주세요.",
            "blank": "비밀번호를 입력해주세요.",
        }
    )

    class Meta:
        model = User
        fields = (
            "password",
            "re_password",
            "confirm_password",
        )
        extra_kwargs = {
            "password": {
                "error_messages": {
                    "required": "비밀번호를 입력해주세요.",
                    "blank": "비밀번호를 입력해주세요.",
                },
            },
        }

    def validate(self, data):
        current_password = self.context.get("request").user.password
        confirm_password = data.get("confirm_password")
        password = data.get("password")
        re_password = data.get("re_password")

        if not check_password(confirm_password, current_password):
            raise serializers.ValidationError(
                detail={"password": "현재 비밀번호가 일치하지 않습니다."})

        if check_password(password, current_password):
            raise serializers.ValidationError(
                detail={"password": "현재 사용중인 비밀번호와 동일한 비밀번호는 입력할 수 없습니다."})

        if password != re_password:
            raise serializers.ValidationError(
                detail={"password": "비밀번호가 일치하지 않습니다."})

        if password_validator(password):
            raise serializers.ValidationError(
                detail={"password": "비밀번호는 8자 이상 16자이하의 영문 대/소문자, 숫자, 특수문자 조합이어야 합니다."})

        if password_pattern(password):
            raise serializers.ValidationError(
                detail={"password": "비밀번호는 3자리 이상 동일한 영문/사용 사용 불가합니다."})

        return data

    def update(self, instance, validated_data):
        instance.password = validated_data.get("password", instance.password)
        instance.set_password(instance.password)
        instance.save()

        return instance


class ResetPasswordEmailSerializer(serializers.Serializer):
    '''
    작성자 : 이주한
    내용 : ResetPasswordEmailView API가 호출될 때 사용되는 시리얼라이저입니다.
            사용자가 입력한 이메일이 존재하는 이메일인지 확인 후 존재할 경우
            로직이 계속되고, 존재하지 않다면 에러 메시지를 띄워줍니다.
            만약 이메일이 존재한다면 해당 이메일 주소로 비밀번호를 변경할 수 있는
            링크를 보냅니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 : 
    '''
    email = serializers.EmailField(
        error_messages={
            "required": "이메일을 입력해주세요.",
            "blank": "이메일을 입력해주세요.",
        }
    )

    class Meta:
        fields = ("email",)

    def validate(self, attrs):
        try:
            email = attrs.get("email")

            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)

            frontend_site = 'https://www.ecocanvas.net'
            absurl = f"{frontend_site}/reset-pw/reset-params?uidb64={uidb64}&token={token}"

            email_body = "비밀번호 재설정을 위해 아래 링크를 클릭해주세요. \n " + absurl
            message = {
                "email_body": email_body,
                "to_email": user.email,
                "email_subject": "비밀번호 재설정",
            }
            Util.send_email(message)

            return super().validate(attrs)

        except User.DoesNotExist:
            raise serializers.ValidationError(
                detail={"email": "잘못된 이메일입니다. 다시 입력해주세요."})


class ResetPasswordSerializer(serializers.Serializer):
    '''
    작성자 : 이주한
    내용 : 사용자가 이메일로 받은 비밀번호 재생성 링크를 통해 페이지에 들어가게 될 경우
            새로운 비밀번호와 새로운 비밀번호를 입력하고 유효성 검증을 거쳐 새로운 
            비밀번호로 비밀번호를 변경합니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 : 
    '''
    password = serializers.CharField(
        error_messages={
            "required": "비밀번호를 입력해주세요.",
            "blank": "비밀번호를 입력해주세요.",
        }
    )
    re_password = serializers.CharField(
        error_messages={
            "required": "비밀번호를 입력해주세요.",
            "blank": "비밀번호를 입력해주세요.",
        }
    )
    token = serializers.CharField(max_length=100, write_only=True)
    uidb64 = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        fields = (
            "password",
            "re_password",
            "token",
            "uidb64",
        )

    def validate(self, attrs):
        password = attrs.get("password")
        re_password = attrs.get("re_password")
        uidb64 = attrs.get("uidb64")
        token = attrs.get("token")
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=user_id)

        if PasswordResetTokenGenerator().check_token(user, token) == False:
            raise exceptions.AuthenticationFailed("링크가 유효하지 않습니다.", 401)

        if password != re_password:
            raise serializers.ValidationError(
                detail={"password": "비밀번호가 일치하지 않습니다."})

        if password_validator(password):
            raise serializers.ValidationError(
                detail={"password": "비밀번호는 8자 이상 16자이하의 영문 대/소문자, 숫자, 특수문자 조합이어야 합니다."})

        if password_pattern(password):
            raise serializers.ValidationError(
                detail={"password": "비밀번호는 3자리 이상 동일한 영문/사용 사용 불가합니다."})

        user.set_password(password)
        user.save()

        return super().validate(attrs)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    '''
    작성자 : 이주한
    내용 : 로그인에 필요한 Custom Token Obtain Pair Serializer 클래스
    최초 작성일 : 2023.06.06
    업데이트 일자 :
    '''
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = user.id
        token["email"] = user.email
        token["is_admin"] = user.is_admin
        token["login_type"] = user.login_type
        return token


class UserSerializer(serializers.ModelSerializer):
    '''
    작성자 : 박지홍
    내용 : 어드민 페이지에서 필요한 유저의 정보를 직렬화 하는 Serializer 클래스
    최초 작성일 : 2023.06.09
    업데이트 일자 :
    '''
    class Meta:
        model = User
        fields = ['id', 'email', 'username',
                  'is_active', 'is_admin', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    '''
    작성자: 장소은
    내용: 유저 프로필 시리얼라이저 
    작성일: 2023.06.17
    '''
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'image', 'address', 'zip_code',
                  'detail_address', 'delivery_message', 'receiver_number']
        extra_kwargs = {
            'image': {'required': False},
            'address': {'required': False},
            'zip_code': {'required': False},
            'detail_address': {'required': False},
            'delivery_message': {'required': False},
            'receiver_number': {'required': False}
        }



