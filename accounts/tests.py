from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthFlowTests(TestCase):
    def test_register_creates_user(self):
        resp = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertRedirects(resp, reverse("accounts:login"))
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_login_open_redirect_prevented(self):
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass123"
        )
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser", "password": "pass123"},
            QUERY_STRING="next=https://evil.com",
        )
        self.assertRedirects(resp, reverse("products:home"))
