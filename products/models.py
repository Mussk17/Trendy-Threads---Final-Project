import uuid
from django.db import models
from django.utils.text import slugify


class Brand(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    material_summary = models.TextField(blank=True)
    care_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not (self.slug and self.slug.strip()):
            self.slug = slugify(self.name) or ''
        if not (self.slug and self.slug.strip()):
            self.slug = f'product-{self.pk}' if self.pk else f'product-{uuid.uuid4().hex[:8]}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_min_price(self):
        """Get minimum price from all variants"""
        variants = self.variants.all()
        if variants.exists():
            return min(v.price for v in variants)
        return 0

    def get_max_price(self):
        """Get maximum price from all variants"""
        variants = self.variants.all()
        if variants.exists():
            return max(v.price for v in variants)
        return 0

    def get_available_sizes(self):
        """Get list of available sizes"""
        return self.variants.values_list('size', flat=True).distinct().order_by('size')

    def get_available_colors(self):
        """Get list of available colors"""
        return self.variants.values_list('color', flat=True).distinct().order_by('color')

    def get_first_color(self):
        """First available color name for UI placeholders (e.g. image fallback)."""
        first = self.get_available_colors().first()
        return first or ""

    def get_first_color_hex(self):
        """Hex for first available color for placeholder strip (UI only)."""
        name = self.get_first_color()
        hex_map = {
            "White": "#f5f5f0", "Ivory": "#fffff0", "Cream": "#fffdd0",
            "Black": "#1a1a1a", "Ink": "#1a1a2e", "Midnight": "#191970",
            "Navy": "#1e3a5f", "Sand": "#c4b8a8", "Natural": "#d4c4a8",
            "Stone": "#b8a88c", "Oat": "#d4c49c", "Sky": "#87ceeb",
            "Charcoal": "#4a4a4a", "Heather Grey": "#6b6b6b", "Gray": "#888", "Grey": "#888",
            "Rose": "#e8b4b8", "Olive": "#6b8e23", "Forest": "#228b22", "Sage": "#9dc183",
            "Khaki": "#c3b091", "Emerald": "#2e8b57", "Rust": "#b7410e", "Camel": "#c19a6b",
            "Indigo": "#4b0082", "Red": "#b84545", "Blue": "#1565c0", "Pink": "#f8bbd9",
            "Brown": "#5d4037", "Beige": "#d4b896", "Tan": "#d2b48c",
        }
        return hex_map.get(name, "#e5e2de")

    def has_low_stock(self):
        """True if any variant has 1-3 items left (for urgency UI)."""
        return self.variants.filter(stock_qty__gt=0, stock_qty__lte=3).exists()

    def get_min_stock_qty(self):
        """Min stock among in-stock variants (for "Only N left" display)."""
        from django.db.models import Min
        return self.variants.filter(stock_qty__gt=0).aggregate(Min('stock_qty'))['stock_qty__min']


class ProductVariant(models.Model):
    SIZES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=10, choices=SIZES)
    color = models.CharField(max_length=50)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty = models.PositiveIntegerField(default=0)
    weight_g = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ['product', 'size', 'color']
        ordering = ['product', 'size', 'color']

    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color}"

    @property
    def is_in_stock(self):
        return self.stock_qty > 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True, related_name='images')
    image_url = models.CharField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"
