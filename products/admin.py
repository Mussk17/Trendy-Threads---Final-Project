from django.contrib import admin
from .models import Brand, Category, Product, ProductVariant, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'country']
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent']
    list_filter = ['parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'get_min_price', 'get_max_price', 'created_at']
    list_filter = ['brand', 'category', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline, ProductImageInline]

    def get_min_price(self, obj):
        return f"${obj.get_min_price()}"
    get_min_price.short_description = 'Min Price'

    def get_max_price(self, obj):
        return f"${obj.get_max_price()}"
    get_max_price.short_description = 'Max Price'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'color', 'price', 'stock_qty', 'sku']
    list_filter = ['size', 'color', 'product__category']
    search_fields = ['product__name', 'sku', 'color']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'variant', 'sort_order', 'alt_text']
    list_filter = ['product__category']
    search_fields = ['product__name', 'alt_text']
