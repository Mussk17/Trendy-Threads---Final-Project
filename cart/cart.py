from decimal import Decimal
from django.conf import settings
from products.models import ProductVariant


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, variant_id, quantity=1):
        """Add a product variant to the cart."""
        try:
            quantity = max(1, int(quantity))
        except (ValueError, TypeError):
            quantity = 1
        variant_id = str(variant_id)
        if variant_id not in self.cart:
            self.cart[variant_id] = {'quantity': 0}
        self.cart[variant_id]['quantity'] += quantity
        self.save()

    def update(self, variant_id, quantity):
        """Update quantity of a variant in the cart"""
        variant_id = str(variant_id)
        if variant_id in self.cart:
            if quantity > 0:
                self.cart[variant_id]['quantity'] = quantity
            else:
                del self.cart[variant_id]
            self.save()

    def remove(self, variant_id):
        """Remove a variant from the cart"""
        variant_id = str(variant_id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        """Iterate over cart items and get the variants from database.
        Yield a copy of each item with variant/product/total_price added; do not
        mutate the session-stored dict (session must remain JSON-serializable).
        """
        variant_ids = list(self.cart.keys())
        variants = ProductVariant.objects.filter(id__in=variant_ids).select_related('product', 'product__brand', 'product__category')
        variant_map = {str(v.id): v for v in variants}
        
        for variant_id, item in self.cart.items():
            if variant_id in variant_map:
                variant = variant_map[variant_id]
                row = dict(item)
                row['variant'] = variant
                row['product'] = variant.product
                row['total_price'] = variant.price * item['quantity']
                yield row

    def __len__(self):
        """Return total number of items in cart"""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calculate total price of items in cart"""
        total = Decimal('0')
        variant_ids = list(self.cart.keys())
        variants = ProductVariant.objects.filter(id__in=variant_ids)
        variant_map = {str(v.id): v for v in variants}
        
        for variant_id, item in self.cart.items():
            if variant_id in variant_map:
                variant = variant_map[variant_id]
                total += variant.price * item['quantity']
        return total

    def get_line_items_for_stripe(self, base_url):
        """Build Stripe line_items from cart. base_url used for images."""
        line_items = []
        variant_ids = list(self.cart.keys())
        variants = ProductVariant.objects.filter(id__in=variant_ids).select_related('product')
        variant_map = {str(v.id): v for v in variants}
        
        for variant_id, item in self.cart.items():
            if variant_id in variant_map:
                variant = variant_map[variant_id]
                product = variant.product
                
                # Get first product image
                img = None
                first_image = product.images.first()
                if first_image:
                    img = base_url + first_image.image_url if not first_image.image_url.startswith('http') else first_image.image_url
                
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f"{product.name} - {variant.size} - {variant.color}",
                            'description': product.description[:500] if product.description else None,
                            'images': [img] if img else None,
                            'metadata': {
                                'product_id': str(product.id),
                                'variant_id': str(variant.id),
                                'size': variant.size,
                                'color': variant.color,
                            },
                        },
                        'unit_amount': int(variant.price * 100),
                    },
                    'quantity': item['quantity'],
                })
        return line_items

    def clear(self):
        """Clear the cart"""
        del self.session[settings.CART_SESSION_ID]
        self.save()
