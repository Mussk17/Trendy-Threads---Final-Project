from django.test import TestCase
from django.urls import reverse


class CheckoutTests(TestCase):
    def test_checkout_redirects_empty_cart(self):
        resp = self.client.get(reverse("orders:checkout"))
        self.assertRedirects(resp, reverse("cart:cart_detail"))
