from django.test import TestCase
from django.urls import reverse


class ChatbotTests(TestCase):
    def test_chat_rejects_empty_question(self):
        resp = self.client.post(
            reverse("chatbot_chat"),
            {"message": ""},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("reply", data)
