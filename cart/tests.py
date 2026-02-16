from django.test import TestCase, Client
from django.urls import reverse
from products.models import Product, ProductVariant, Brand, Category


class CartTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name="Test", country="UK")
        cat = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            name="Test Product", slug="test-prod", brand=brand, category=cat, description="Test"
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, size="M", color="Black", sku="TEST-M-BLK", price=29.99, stock_qty=5
        )

    def test_cart_add_validates_quantity(self):
        resp = self.client.post(
            reverse("cart:cart_add", args=[self.variant.id]),
            {"quantity": -5},
        )
        session_cart = self.client.session.get("cart", {})
        self.assertEqual(session_cart.get(str(self.variant.id), {}).get("quantity", 0), 1)
