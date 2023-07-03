from django.urls import path
from users import views


urlpatterns = [
    # 회원가입
    path('signup/', views.SignUpView.as_view(), name='sign_up'),
    path('signup/email_code/', views.SendSignupEmailView.as_view(), name='send_email'),
    path('oauth/kakao/callback/',
         views.KakaoCallbackView.as_view(), name='kakao_callback'),
    path('kakao/login/finish/', views.KakaoLogin.as_view(),
         name='kakao_login_todjango'),
    path('google/login/', views.GoogleLoginFormView.as_view(), name='google_login'),
    path('google/callback/', views.GoogleCallbackView.as_view(),
         name='google_callback'),

    # 회원정보 관련
    path('', views.UserView.as_view(), name='update_or_withdrawal'),

    # 비밀번호 수정 관련
    path('update_pw/', views.UpdatePasswordView.as_view(), name='update_password'),
    path('reset_pw/', views.ResetPasswordView.as_view(), name='reset_password'),
    path("reset_pw/<uidb64>/<token>/", views.CheckPasswordTokenView.as_view(),
         name="reset_password_token_check"),
    path('reset_pw/email_code/', views.ResetPasswordEmailView.as_view(),
         name='reset_password_email'),

    # 로그인
    path('login/', views.CustomTokenObtainPairView.as_view(), name='log_in'),
    path('list/', views.UserListView().as_view(), name='user_list'),
    path('<int:user_id>/', views.UserDetailView().as_view(), name='user'),

    # 유저프로필
    path('profile/', views.UserProfileAPIView.as_view(), name='user_profile'),
]
