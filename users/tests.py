from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import smart_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from users.models import User, UserProfile
from users.serializers import UserSerializer


class SendSignupEmailTest(APITestCase):
    def setUp(self):
        self.email = 'test@example.com'
        self.user = User.objects.create_user(
            username='test_user',
            email=self.email,
            password='test_password'
        )
        self.user.withdrawal = True
        self.user.save()

    def test_post_with_withdrawal_true(self):
        url = reverse("send_email")
        data = {
            'email': self.email,
            'time_check': '202377'
        }

        response = self.client.post(url, data, format ='json')
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        self.assertEqual(response.data['withdrawal_true'], '계정이 재활성화 되었습니다. 로그인을 진행해 주세요!')

        user = User.objects.get(email=self.email)
        self.assertFalse(user.withdrawal)
        self.assertTrue(user.is_active)

    def test_post_with_invalid_data(self):
        url = reverse("send_email")
        data = {
            'email': '',
            'time_check': '202377'
        }

        response = self.client.post(url, data, format ='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_post_with_valid_data(self):
        url = reverse("send_email")
        data = {
            'email': 'test2@example.com',
            'time_check': '202377'
        }

        response = self.client.post(url, data, format ='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '이메일 인증코드를 회원님의 이메일 계정으로 발송했습니다. 확인 부탁드립니다!')

class SignUpTest(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.06.07
    작성내용 : 회원가입시 발생할 수 있는 이슈들에 관한 테스트 코드
    업데이트 날짜 : 
    '''
    def test_signup(self):
        url = reverse("sign_up")
        user_data = {
            "email": "user1@google.com",
            "check_code": "7b489ac24a57ef6782f367e8190d839501de46e2f770e7ef74afd5dc9b09660c",
            "username": "user1",
            "password": "Test!!11",
            "re_password": "Test!!11",
            "time_check": "202374"
        }
        response = self.client.post(url, user_data)
        self.assertEqual(response.status_code, 201)
    
    def test_signup_wrong_password_validate(self):
        url = reverse("sign_up")
        user_data = {
            "email": "user1@google.com",
            "check_code": "7b489ac24a57ef6782f367e8190d839501de46e2f770e7ef74afd5dc9b09660c==",
            "username": "user1",
            "password": "test11",
            "re_password": "test11",
            "time_check": "202374"
        }
        response = self.client.post(url, user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_signup_wrong_password_pattern(self):
        url = reverse("sign_up")
        user_data = {
            "email": "user1@google.com",
            "check_code": "7b489ac24a57ef6782f367e8190d839501de46e2f770e7ef74afd5dc9b09660c==",
            "username": "user1",
            "password": "tttTTT111!!!",
            "re_password": "tttTTT111!!!",
            "time_check": "202374"
        }
        response = self.client.post(url, user_data)
        self.assertEqual(response.status_code, 400)
    
    def test_signup_none_re_password(self):
        url = reverse("sign_up")
        user_data = {
            "email": "user1@google.com",
            "check_code": "7b489ac24a57ef6782f367e8190d839501de46e2f770e7ef74afd5dc9b09660c==",
            "username": "user1",
            "password": "Test!!11",
            "time_check": "202374"
        }
        response = self.client.post(url, user_data)
        self.assertEqual(response.status_code, 400)

    def test_signup_none_check_code(self):
        url = reverse("sign_up")
        user_data = {
            "email": "user1@google.com",
            "check_code": "",
            "username": "user1",
            "password": "Test!!11",
            "re_password": "Test!!11",
            "time_check": "202374"
        }
        response = self.client.post(url, user_data)
        self.assertEqual(response.status_code, 400)

class LoginTest(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.06.07
    작성내용 : 로그인시 발생할 수 있는 이슈들에 관한 테스트 코드
    업데이트 날짜 : 
    '''
    def setUp(self):
        self.url = reverse('log_in')
        self.user_data = User.objects.create_user(email="user1@google.com", username="test", password="Test!!11")
        
    def test_login(self):
        user ={
            "email": "user1@google.com",
            "password":"Test!!11",
        }
        response = self.client.post(self.url, user, format='json')
        self.assertEqual(response.status_code, 200)

    def test_login_wrong_password(self):
        user ={
            "email": "user1@google.com",
            "password":"test!!11",
        }
        response = self.client.post(self.url, user, format='json')
        self.assertEqual(response.status_code, 401)
    
    
class UserListTest(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.06.16
    작성내용 : 회원정보 조회 시 발생할 수 있는 경우들을 테스트합니다.
    업데이트 날짜 : 
    '''
    def setUp(self):
        self.data = {'email': 'user1@google.com', "password": "Test!!11"}
        self.user = User.objects.create_user(email="user1@google.com", username="test", password="Test!!11")

    def test_get_user_data(self):
        access_token = self.client.post(reverse('log_in'), self.data).data["access"]
        response = self.client.get(
            path=reverse("user_list"),
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, 200)


class UserUpdateWithdrawalTest(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.06.16
    작성내용 : 회원정보 수정 or 회원 비활성화 시 발생할 수 있는 경우들을 테스트합니다.
    업데이트 날짜 : 
    '''
    def setUp(self):
        self.data = {'email': 'user1@google.com', "password": "Test!!11"}
        self.user = User.objects.create_user(email="user1@google.com", username="test", password="Test!!11")

    def test_update_user(self):
        access_token = self.client.post(reverse('log_in'), self.data).data["access"]
        response = self.client.put(
            path=reverse("update_or_withdrawal"),
            data={'email': 'user11@google.com'},
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, 200)
    
    def test_withdrawal_user(self):
        access_token = self.client.post(reverse('log_in'), self.data).data["access"]
        response = self.client.delete(
            path=reverse("update_or_withdrawal"),
            data={'confirm_password': self.data["password"]},
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, 200)


class PasswordUpdateTest(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.06.16
    작성내용 : 비밀번호 수정 시 발생할 수 있는 경우들을 테스트합니다.
    업데이트 날짜 : 
    '''
    def test_password_update(self):
        User.objects.create_user(email="user1@google.com", username="test", password="Test!!11")
        access_token = self.client.post(reverse('log_in'), {'email': 'user1@google.com', "password": "Test!!11"}).data["access"]
        response = self.client.put(
            path=reverse("update_password"),
            data={
                "confirm_password": "Test!!11",
                "password": "Test@@22",
                "re_password": "Test@@22"
            },
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, 200)


class PasswordResetTest(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.06.16
    작성내용 : 비밀번호 재설정 시 발생할 수 있는 경우들을 테스트합니다.
    업데이트 날짜 : 
    '''
    def setUp(self):
        self.user = User.objects.create_user("user1@google.com", "test", "Test1234!")
        self.uidb64 = urlsafe_base64_encode(smart_bytes(self.user.id))
        self.token = PasswordResetTokenGenerator().make_token(self.user)
        
    
    def test_password_reset(self):
        response = self.client.put(
            path=reverse("reset_password"),
            data={
                "password": "Test1234!!",
                "re_password": "Test1234!!",
                "uidb64": self.uidb64,
                "token": self.token
            },
        )
        self.assertEqual(response.status_code, 200)
    
    def test_password_reset_blank_fail(self):
        response = self.client.put(
            path=reverse("reset_password"),
            data={
                "password": "",
                "re_password": "Test1234!!",
                "uidb64": self.uidb64,
                "token": self.token
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_password_reset_confirm_blank_fail(self):
        response = self.client.put(
            path=reverse("reset_password"),
            data={
                "password": "Test1234!!",
                "re_password": "",
                "uidb64": self.uidb64,
                "token": self.token
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_password_reset_validation_fail(self):
        response = self.client.put(
            path=reverse("reset_password"),
            data={
                "password": "Test1234",
                "re_password": "Test1234",
                "uidb64": self.uidb64,
                "token": self.token
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_password_reset_validation_same_fail(self):
        response = self.client.put(
            path=reverse("reset_password"),
            data={
                "password": "Test111!",
                "re_password": "Test111!",
                "uidb64": self.uidb64,
                "token": self.token
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_password_reset_same_fail(self):
        response = self.client.put(
            path=reverse("reset_password"),
            data={
                "password": "Test1234!!",
                "re_password": "Test1234!",
                "uidb64": self.uidb64,
                "token": self.token
            },
        )
        self.assertEqual(response.status_code, 400)


class PasswordResetEmailTest(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.06.16
    작성내용 : 비밀번호 찾기(재설정) 인증코드 발급을 위한 이메일 전송 시 발생할 수 있는 경우들을 테스트합니다.
    업데이트 날짜 : 
    '''
    def setUp(self):
        self.user = User.objects.create_user("user1@google.com", "test", "Test1234!")
    
    def test_password_reset_email(self):
        response = self.client.post(
            path=reverse("reset_password_email"), 
            data={"email": "user1@google.com"},
        )
        self.assertEqual(response.status_code, 200)
    
    def test_password_reset_email_fail(self):
        response = self.client.post(
            path=reverse("reset_password_email"), 
            data={"email": "user2@google.com"},
        )
        self.assertEqual(response.status_code, 400)

    def test_password_reset_email_blank_fail(self):
        response = self.client.post(
            path=reverse("reset_password_email"), 
            data={"email": ""},
        )
        self.assertEqual(response.status_code, 400)


class PasswordResetCheckToken(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.06.16
    작성내용 : 비밀번호 찾기(재설정) 인증코드가 유효한지 확인 시 발생할 수 있는 경우들을 테스트합니다.
    업데이트 날짜 : 
    '''
    def setUp(self):
        self.user = User.objects.create_user("user1@google.com", "test", "Test1234!")
        self.uidb64 = urlsafe_base64_encode(smart_bytes(self.user.id))
        self.token = PasswordResetTokenGenerator().make_token(self.user)
    
    def test_password_reset_check_token(self):
        response = self.client.get(
            path=reverse("reset_password_token_check",kwargs={"uidb64": self.uidb64, "token": self.token},),
        )
        self.assertEqual(response.status_code, 200)
    
    def test_password_reset_check_token_fail(self):
        response = self.client.get(
            path=reverse("reset_password_token_check", kwargs={"uidb64": "uidb64", "token": "token"})
        )
        self.assertEqual(response.status_code, 401)


class UserListViewTestCase(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.07.04
    작성내용 : 어드민 페이지에서 전체 사용자 리스트를 조회할 시 발생할 수 있는 경우들을 테스트합니다.
    업데이트 날짜 : 
    '''
    def setUp(self):
        User.objects.create(email='user1@google.com', username='user1', password='Test!!11')
        User.objects.create(email='user2@google.com', username='user2', password='Test@@22')
        User.objects.create(email='user3@google.com', username='user3', password='Test##33')

    def test_user_list_view(self):
        response = self.client.get(reverse('user_list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in response.data)
        self.assertTrue('count' in response.data)
        self.assertEqual(len(response.data['results']), 3)

        serializer = UserSerializer(User.objects.all(), many=True)
        self.assertEqual(response.data['results'], serializer.data)


class UserDetailViewTestCase(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.07.04
    작성내용 : 어드민 페이지에서 사용자의 상세 정보를 조회하거나 권한을 변경할 시 발생할 수 있는 경우들을 테스트합니다.
    업데이트 날짜 : 
    '''
    def setUp(self):
        self.user = User.objects.create(email='user1@google.com', username='user1', password='Test!!11', is_admin=False)

    def test_get_user_detail(self):
        url = f'/users/{self.user.id}/'
        response = self.client.get(url)

        # 테스트 결과 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, UserSerializer(self.user).data)

    def test_toggle_user_admin(self):
        url = f'/users/{self.user.id}/'
        response = self.client.put(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(response.data['is_admin'], self.user.is_admin)


class UserProfileTestCase(APITestCase):
    '''
    작성자 : 이주한
    작성날짜 : 2023.07.04
    작성내용 : 사용자의 프로필을 조회하거나 수정할 시 발생할 수 있는 경우들을 테스트합니다.
    업데이트 날짜 : 
    '''
    def setUp(self):
        self.user = User.objects.create_user(email='user1@google.com', username='user1', password='Test!!11')
        self.user_profile = UserProfile.objects.get(user=self.user)
        self.client.force_authenticate(user=self.user)

    def test_get_user_profile(self):
        response = self.client.get(reverse('user_profile'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], self.user.username)
        self.assertEqual(response.data['image'], None)
        self.assertEqual(response.data['address'], None)
        self.assertEqual(response.data['zip_code'], None)
        self.assertEqual(response.data['detail_address'], None)
        self.assertEqual(response.data['delivery_message'], None)
        self.assertEqual(response.data['receiver_number'], None)

    def test_update_user_profile(self):
        response = self.client.put(
            path=reverse('user_profile'),
            data = {
                'address': 'New Address',
                'zip_code': '54321',
                'detail_address': 'New Detail Address',
                'delivery_message': 'New Delivery Message',
                'receiver_number': '010-9876-5432'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_profile.refresh_from_db()
        self.assertEqual(self.user_profile.address, 'New Address')
        self.assertEqual(self.user_profile.zip_code, '54321')
        self.assertEqual(self.user_profile.detail_address, 'New Detail Address')
        self.assertEqual(self.user_profile.delivery_message, 'New Delivery Message')
        self.assertEqual(self.user_profile.receiver_number, '010-9876-5432')
