from django.test import TestCase
from user.models import User, Ticket
from unittest.mock import patch
from django.urls import reverse
from django.core import mail
from .serializers import LoginSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class SignUpPageTests(TestCase):
    
    # 셋업
    def setUp(self) -> None:
        self.nickname = "testuser"
        self.email = "testuser@email.com"
        self.password = "1234567!"
        self.wrongpassword = "1234567~"
        self.country = "미국"

    # 올바른 회원가입
    def test_signup_form(self):
        response = self.client.post(
            reverse("register_view"),
            data={
                "nickname": self.nickname,
                "email": self.email,
                "password": self.password,
                "password_check": self.password,
                "country": self.country,
            },
        )
        users = User.objects.all()
        self.assertEqual(users.count(), 1)
        self.assertEqual(response.status_code, 201)

        # Celery 작업이 예상대로 호출되었는지 확인
        with self.settings(CELERY_ALWAYS_EAGER=True):
            # 작업 실행 확인
            with patch('user.tasks.send_verification_email.delay') as mock_celery_task:

                user = User.objects.get(email=self.email)

                # 회원가입 이메일 확인 작업 호출
                mock_celery_task(user.id, 'verification_url', user.email)

                # 호출 확인
                mock_celery_task.assert_called_with(user.id, 'verification_url', user.email)

                # 이메일 정보 확인
                self.assertEqual(len(mail.outbox), 1)  # 이메일 보내졌는지 확인

                email = mail.outbox[0]
                print(email)
                print(email.to)
                print(email.subject)
                print(email.body)


    # 틀린 회원가입
    def test_wrong_signup_form(self):
        response = self.client.post(
            reverse("register_view"),
            data={
                "nickname": self.nickname,
                "email": self.email,
                "password": self.password,
                "password_check": self.wrongpassword,
                "country": self.country,
            },
        )
        self.assertEqual(response.status_code, 400)

        users = User.objects.all()
        self.assertEqual(users.count(), 0)


class LoginTests(TestCase):
    @classmethod
    # 셋업
    def setUpTestData(cls):
        member = {
            "email": "testuser@email.com",
            "nickname": "testuser",
            "country": "미국",
            "password": "1234567!",
        }
        cls.user = User.objects.create_user(**member)
        cls.user.is_active = True
        cls.user.save()

    # 로그인
    def test_token(self):
        response = self.client.post(
            reverse("login_view"),
            data={
                "email": "testuser@email.com",
                "password": "1234567!",
            },
        )
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        self.assertFalse(access_token == "")
        self.assertFalse(refresh_token == "")

    # 마이페이지 GET
    def test_mypage(self):
        access_token = self.client.post(
            reverse("login_view"),
            data={
                "email": "testuser@email.com",
                "password": "1234567!",
            },
        ).data["access"]
        response = self.client.get(
            path=reverse("mypage_view"),
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["my_data"]["email"], "testuser@email.com")
        self.assertEqual(response.data["my_data"]["nickname"], "testuser")
        self.assertEqual(response.data["my_data"]["country"], "미국")


class UserInfoTest(TestCase):
    @classmethod
    # 셋업
    def setUpTestData(cls):
        member = {
            "email": "testuser@email.com",
            "nickname": "testuser",
            "country": "미국",
            "password": "1234567!",
        }
        cls.user = User.objects.create_user(**member)
        cls.user.is_active = True
        cls.user.save()

        response = LoginSerializer(data=member)
        try:
            response.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        cls.access_token = response.validated_data["access"]

    # 유저 정보 수정 페이지 GET
    def get_user_info_test(self):
        response = self.client.get(
            reverse("user_info_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user_info"]["country"], "미국")
        self.assertEqual(response.data["user_info"]["nickname"], "testuser")

    # 유저 정보 수정 PUT
    def put_user_info_test(self):
        response = self.client.put(
            reverse("user_info_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={
                "nickname": "testuser2",
                "country": "대한민국",
            },
        )
        user = User.objects.get(email="testuser@email.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.nickname, "testuser2")
        self.assertEqual(user.country, "대한민국")

    # 유저 회원 탈퇴 DELETE
    def delete_user_info_test(self):
        response = self.client.delete(
            reverse("user_info_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={"password": "1234567!"},
        )
        users = User.objects.all()
        self.assertEqual(users.count(), 0)
        self.assertEqual(response.status_code, 204)

    # 유저 비밀번호 변경 PATCH
    def patch_user_info_test(self):
        response = self.client.patch(
            reverse("user_info_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={
                "current_password": "1234567!",
                "new_password": "1234567~",
                "new_password_check": "1234567~",
            },
        )
        self.assertEqual(response.status_code, 200)
        # 수정된 비밀번호로 로그인 확인
        response = self.client.post(
            reverse("login_view"),
            data={
                "email": "testuser@email.com",
                "password": "1234567~",
            },
        )
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        self.assertFalse(access_token == "")
        self.assertFalse(refresh_token == "")


class PaymentTest(TestCase):
    @classmethod
    # 셋업
    def setUpTestData(cls):
        member = {
            "email": "testuser@email.com",
            "nickname": "testuser",
            "country": "미국",
            "password": "1234567!",
        }
        cls.user = User.objects.create_user(**member)
        cls.user.is_active = True
        cls.user.save()
        Ticket.objects.create(ticket_owner=cls.user)
        response = LoginSerializer(data=member)
        try:
            response.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        cls.access_token = response.validated_data["access"]

    # 주문 정보 페이지 로드
    def payment_payge_view_test(self):
        response = self.client.post(
            reverse("payment_page_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={
                "amount": "2000",
                "name": "G5_S5_P5",
            },
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("payment_page_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={
                "amount": "20000",
                "name": "G5_S5_P5",
            },
        )
        self.assertEqual(response.status_code, 400)

    def payment_result_view_test(self):
        cur_ticket = Ticket.objects.get(ticket_owner=self.user)
        cur_pink = cur_ticket.pink_ticket
        cur_silver = cur_ticket.silver_ticket
        cur_golden = cur_ticket.golden_ticket

        response = self.client.post(
            reverse("payment_result_view"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
            data={
                "rsp": {
                    "buyer_email": "testuser@email.com",
                    "buyer_name": "testuser",
                    "name": "G1_S1_P1",
                    "paid_amount": "2000",
                    "currency": "US",
                    "pg_provider": "kakaopay",
                    "pg_tid": "1",
                    "pay_method": "point",
                    "back_name": "",
                    "card_name": "",
                    "card_number": "",
                    "receipt_url": "",
                    "status": "paid",
                }
            },
        )
        self.assertEqual(response.status_code, 201)
        next_ticket = Ticket.objects.get(ticket_owner=self.user)
        next_pink = next_ticket.pink_ticket
        next_silver = next_ticket.silver_ticket
        next_golden = next_ticket.golden_ticket
        self.assertEqual(next_pink - cur_pink, 1)
        self.assertEqual(next_silver - cur_silver, 1)
        self.assertEqual(next_golden - cur_golden, 1)

    def ticket_view_test(self):
        user_ticket = Ticket.objects.get(ticket_owner=self.user)
        user_pink = user_ticket.pink_ticket
        user_silver = user_ticket.silver_ticket
        user_golden = user_ticket.golden_ticket
        response = self.client.get(
            reverse("user_tickets"),
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pink_ticket_count"], user_pink)
        self.assertEqual(response.data["silver_ticket_count"], user_silver)
        self.assertEqual(response.data["golden_ticket_count"], user_golden)
