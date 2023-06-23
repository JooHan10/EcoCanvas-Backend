from users.models import User, UserProfile, Notification
import requests
import os
import base64
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import redirect
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from users.serializers import (
    SignUpSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UpdatePasswordSerializer,
    ResetPasswordSerializer,
    ResetPasswordEmailSerializer,
    UserProfileSerializer,
    UserNotificationSerializer
)
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.kakao import views as kakao_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.http import JsonResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.encoding import DjangoUnicodeDecodeError, force_str
from django.utils.http import urlsafe_base64_decode
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

state = os.environ.get('STATE')
kakao_callback_uri = os.environ.get('KAKAO_CALLBACK_URI')
google_callback_uri = os.environ.get('GOOGLE_CALLBACK_URI')
base_url = os.environ.get('BASE_URL')
front_base_url = os.environ.get('FRONT_BASE_URL')
secret_key = os.environ.get('SECRET_KEY')


def verification_code(email):
    '''
    작성자 : 이주한
    내용 : 회원가입시 이메일 인증에 필요한 인증 코드를 생성하는 함수입니다.
            개발 단계에서는 필요하지 않을 수 있어 주석 처리해 두었습니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 :
    '''
    email_bytes = email.encode('ascii')
    email_base64 = base64.b64encode(email_bytes)
    email_base64_str = email_base64.decode('ascii')
    return email_base64_str


class SendEmailView(APIView):
    '''
    작성자 : 이주한
    내용 : 회원가입시 이메일 인증에 필요한 메일을 보내는 view 클래스입니다.
            개발 단계에서는 이메일 인증이 번거로울 수 있어 주석 처리해 두었습니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 :
    '''

    def post(self, request):
        email = request.data.get("email")
        if email == "":
            return Response({'error': '이메일을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                User.objects.get(email=email)
                return Response({"message": "계정이 이미 존재합니다."}, status=status.HTTP_400_BAD_REQUEST)
            except:
                subject = 'EcoCanvas 인증 코드 메일'
                body = verification_code(email)
                email_content = EmailMessage(subject, body, to=[email],)
                email_content.send()
                return Response({"message": "귀하의 이메일에서 인증코드를 확인해주세요."}, status=status.HTTP_200_OK)


class SignUpView(APIView):
    '''
    작성자 : 이주한
    내용 : 회원가입에 사용되는 view 클래스 입니다.
            개발 단계에서는 이메일 인증이 번거로울 수 있어 주석 처리해 두었습니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.15
    '''

    def post(self, request):
        if verification_code(request.data.get("email")) != request.data.get("check_code"):
            return Response({"message": f"잘못된 인증코드입니다."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "가입완료!"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    '''
    작성자 : 이주한
    내용 : 회원정보 수정, 회원 비활성화에 사용되는 view 클래스
    최초 작성일 : 2023.06.06
    업데이트 일자 : 2023.06.14
    '''

    def put(self, request):
        user = get_object_or_404(User, id=request.user.id)
        serializer = UserUpdateSerializer(
            user, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "회원정보 수정이 완료되었습니다."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = get_object_or_404(User, id=request.user.id)
        user.withdrawal = True
        user.withdrawal_at = timezone.now()
        user.save()
        return Response({"message": "회원이 비활성화 되었습니다."}, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    '''
    작성자 : 이주한
    내용 : 로그인에 사용되는 JWT 토큰 view 입니다.
    최초 작성일 : 2023.06.06
    업데이트 일자 :
    '''
    serializer_class = CustomTokenObtainPairSerializer


class CustomRefreshToken(RefreshToken):
    '''
    작성자 : 장소은
    내용 : 사용자에 대한 새로운 토큰을 생성하는 클래스. 사용자의 ID와 이메일 정보를 토큰에 추가하여 반환
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    '''
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token["user_id"] = user.id
        token['email'] = user.email
        token['is_admin'] = user.is_admin
        return token


def generate_jwt_token(user):
    '''
    작성자 : 장소은
    내용: 사용자를 인자로 받아 RefreshToken을 생성. 'refresh'와 'access'라는 키로 구성된 딕셔너리 형태의 문자열 토큰 반환
    최초 작성일 : 2023.06.08
    업데이트 일자 :
    '''
    refresh = CustomRefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class GoogleLoginFormView(APIView):
    def get(self, request):
        '''
        작성자 : 이주한
        내용 : 구글 OAUTH2.0 서버로 client_id, callback_uri, scope를 보내서 구글 로그인 페이지를 불러옵니다.
        최초 작성일 : 2023.06.08
        업데이트 일자 : 2023.06.19
        '''
        scope = "profile%20email"
        client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")

        return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={google_callback_uri}&scope={scope}")


class GoogleCallbackView(APIView):
    '''
    작성자 : 이주한
    내용 : 받아온 구글 로그인 폼에 사용자가 id와 pw를 작성하여 제공하면 구글이 Authorization Code를 발급해줍니다.
            Authorization Code를 활용하여 우리의 앱이 API에 사용자의 정보를 요청하여 받아옵니다.
            해당 정보들 중 email을 사용하여 사용자를 확인하고 JWT token을 발급받아 로그인을 진행합니다.
    최초 작성일 : 2023.06.08
    업데이트 일자 : 2023.06.19
    '''

    def post(self, request):
        client_id = os.environ.get("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("SOCIAL_AUTH_GOOGLE_SECRET")
        authorization_code = request.GET.get('code')

        access_token_request = requests.post(
            "https://oauth2.googleapis.com/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "code": authorization_code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": google_callback_uri,
                "grant_type": "authorization_code",
                "scope": "email",
            },
        )
        access_token_json = access_token_request.json()
        access_token = access_token_json.get("access_token")

        user_data_request = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data_json = user_data_request.json()
        email = user_data_json.get("email")
        username = user_data_json.get("name")

        try:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            refresh["email"] = user.email

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )
        except:
            user = User.objects.create_user(email=email, username=username)
            user.set_unusable_password()
            user.save()
            refresh = RefreshToken.for_user(user)
            refresh["email"] = user.email

            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
            )


class KakaoCallbackView(APIView):
    '''
    작성자 : 장소은
    내용 :  Kakao 로그인 콜백을 처리하는 APIView GET. Kakao 토큰 API에 POST 요청을 보냄.
            응답을 받아와서 JSON 형식으로 파싱하여 access_token추출
            응답 데이터에 'error' 키가 포함되어 있다면 에러처리.
            그렇지 않은 경우는 access_token을 사용하여 Kakao API를 호출하여 사용자 정보를 가져옴 이메일(kakao_email), 연령대(age_range), 성별(gender) 추출
            try-except - 기존에 가입된 유저인지 체크
            만약 가입된 유저라면, 해당 유저정보를 사용하여 JWT 토큰을 생성하고, 리다이렉트 응답&JWT 토큰은 쿠키에 저장해 전달
            User.DoesNotExist - 새로운 가입자 처리, 가입 처리 결과에 따라 리다이렉트 응답을 생성
            +) RedirectURL과 쿠키 반환 로직 변경
    최초 작성일 : 2023.06.08
    업데이트 일자 : 2023.06.11
    '''
    permission_classes = [AllowAny]

    def get(self, request):
        rest_api_key = os.environ.get('KAKAO_REST_API_KEY')
        restapikey = rest_api_key
        code = request.GET.get("code")
        redirect_uri = kakao_callback_uri
        token_req = requests.get(
            f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={restapikey}&redirect_uri={redirect_uri}&code={code}"
        )
        token_req_json = token_req.json()
        error = token_req_json.get("error")
        if error is not None:
            redirect_url = front_base_url
            err_msg = error
            redirect_url_with_status = f'{redirect_url}?err_msg={err_msg}'
            return redirect(redirect_url_with_status)
        access_token = token_req_json.get("access_token")
        profile_request = requests.post(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_json = profile_request.json()
        error = profile_json.get("error")
        if error is not None:
            redirect_url = front_base_url
            err_msg = error
            redirect_url_with_status = f'{redirect_url}?err_msg={err_msg}'
            return redirect(redirect_url_with_status)
        kakao_user_info = profile_json.get('kakao_account')
        kakao_email = kakao_user_info["email"]
        age_range = kakao_user_info["age_range"]
        gender = kakao_user_info["gender"]

        try:
            # 기존에 가입된 유저의 Provider가 kakao가 아니면 에러 발생, 맞으면 로그인
            # 다른 SNS로 가입된 유저
            user = User.objects.get(email=kakao_email)
            social_user = SocialAccount.objects.get(user=user)

            if social_user is None:
                redirect_url = front_base_url
                status_code = 204
                redirect_url_with_status = f'{redirect_url}?status_code={status_code}'
                return redirect(redirect_url_with_status)
            if social_user.provider != 'kakao':
                redirect_url = front_base_url
                status_code = 400
                redirect_url_with_status = f'{redirect_url}?status_code={status_code}'
                return redirect(redirect_url_with_status)
            # 기존에 kakao로 가입된 유저
            data = {"access_token": access_token, "code": code}
            accept = requests.post(
                f"{base_url}/users/kakao/login/finish/", data=data)
            accept_status = accept.status_code
            if accept_status != 200:
                return JsonResponse({"err_msg": "failed to signin"}, status=accept_status)
            jwt_token = generate_jwt_token(user)
            response_data = {
                'jwt_token': jwt_token
            }
            return JsonResponse(response_data)

        except ObjectDoesNotExist:
            # 기존에 가입된 유저가 없으면 새로 가입
            data = {"access_token": access_token, "code": code}
            accept = requests.post(
                f"{base_url}/users/kakao/login/finish/", data=data)
            accept_status = accept.status_code

            if accept_status != 200:
                redirect_url = front_base_url
                status_code = accept_status
                err_msg = "kakao_signup"
                redirect_url_with_status = f'{redirect_url}?err_msg={err_msg}'
                return redirect(redirect_url_with_status)

            redirect_url = front_base_url
            status_code = 201
            redirect_url_with_status = f'{redirect_url}?status_code={status_code}'
            return redirect(redirect_url_with_status)


class KakaoLogin(SocialLoginView):
    '''
    작성자 : 장소은
    내용: Kakao OAuth2 어댑터와 OAuth2Client를 사용하여 Kakao 로그인을 처리하는 클래스. 인증 완료 후 SocialLoginView에서 처리되는 방식
    작성일 : 2023.06.08
    업데이트 일자 :
    '''
    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = kakao_callback_uri


class UserListView(APIView):
    '''
    작성자 : 박지홍
    내용: 어드민 페이지에서 전체 일반 유저 리스트를 받기 위해 사용
    작성일 : 2023.06.09
    업데이트 일자 :
    '''

    def get(self, request):
        users = User.objects.filter(is_admin=False)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    '''
    작성자 : 박지홍
    내용: 어드민 페이지에서 일반 유저의 상세 정보를 알기 위해 사용
    작성일 : 2023.06.09
    업데이트 일자 :
    '''

    def get(self, request, user_id):
        user = User.objects.filter(id=user_id)
        serializer = UserSerializer(user, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdatePasswordView(APIView):
    '''
    작성자 : 이주한
    내용 : 사용자가 로그인한 상태에서 본인 계정의 비밀번호를 수정할 때 사용되는 UpdatePasswordView 입니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 :
    '''
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = get_object_or_404(User, id=request.user.id)
        serializer = UpdatePasswordSerializer(
            user, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "비밀번호 변경이 완료되었습니다. 다시 로그인해주세요!"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    '''
    작성자 : 이주한
    내용 : 사용자가 비밀번호를 분실했을 시 비밀번호를 변경할 수 있도록 비밀번호를 재설정하는 ResetPasswordView 입니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 :
    '''
    permission_classes = [AllowAny]

    def put(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "비밀번호 재설정 완료"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordEmailView(APIView):
    '''
    작성자 : 이주한
    내용 : 사용자가 비밀번호를 분실했을 시 비밀번호를 변경할 수 있도록
            비밀번호를 재설정하는 링크를 사용자의 메일로 보내줍니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 :
    '''
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordEmailSerializer(
            data=request.data, context={"request": request})
        if serializer.is_valid():
            return Response({"message": "비밀번호 재설정 이메일을 발송했습니다. 확인부탁드립니다."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckPasswordTokenView(APIView):
    '''
    작성자 : 이주한
    내용 : 사용자가 받은 비밀번호 재설정 링크를 클릭했을 시
            유효한 링크인지 링크에 담겨진 url 파라미터 값으로 검증을 합니다.
    최초 작성일 : 2023.06.15
    업데이트 일자 :
    '''
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))

            user = get_object_or_404(User, pk=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({"message": "링크가 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({"uidb64": uidb64, "token": token}, status=status.HTTP_200_OK)

        except DjangoUnicodeDecodeError as identifier:
            return Response({"message": "링크가 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileAPIView(APIView):
    '''
    작성자 : 장소은
    내용 : (기존) 작성된 로직은 유저의 프로필이 없다면 생성하도록 만들고 그에 해당하는 예외처리
          (수정) signals.py에서 receiver를 통해 유저 생성 시 프로필 생성되도록 변경하고 그로 인해 불필요한 코드 삭제
    작성일 : 2023.06.15
    업데이트일 : 2023.06.21
    '''

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(
            instance=user_profile, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "회원정보 수정 완료!"}, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class CustomPagination(PageNumberPagination):
    '''
    작성자: 장소은
    내용 : 페이지네이션을 위한 커스텀페이지네이션
    작성일: 2023.06.16
    '''
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 60


class NotificationListAPIView(APIView):
    '''
    작성자 : 장소은
    내용 : 유저 캠페인 알림/재입고 알림 조회 기능, 개별 삭제/일괄 삭제 기능 
    작성일 : 2023.06.22
    '''
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request):
        notifications = Notification.objects.all().order_by('-created_at')
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(notifications, request)
        serializer = UserNotificationSerializer(
            result_page,
            many=True
        )
        return paginator.get_paginated_response(serializer.data)

    def delete(self, request):
        user = request.user.id
        notification_id = request.data.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(
                    Q(participant__user__id=user) |
                    Q(restock__user__id=user),
                    id=notification_id
                )
                notification.delete()
                return Response(status=204)

            except Notification.DoesNotExist:
                return Response({'error': '알림내역을 찾을 수 없습니다.'}, status=404)

        else:
            notifications = Notification.objects.filter(
                Q(participant__user__id=user) |
                Q(restock__user__id=user)
            )
            notifications.delete()
            return Response(status=204)
