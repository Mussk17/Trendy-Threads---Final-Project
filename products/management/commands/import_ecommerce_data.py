import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from products.models import Brand, Category, Product, ProductVariant, ProductImage


class Command(BaseCommand):
    help = 'Import ecommerce data from CSV files in data/seed_data/ (default) or specified directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing',
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            default='data/seed_data',
            help='Path to directory containing CSV files (relative to project root)',
        )

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        
        # Resolve absolute path
        if not os.path.isabs(data_dir):
            # Get project root (where manage.py is located)
            # __file__ is: trendy-threads/products/management/commands/import_ecommerce_data.py
            # Go up 4 levels to get to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            data_dir = os.path.join(base_dir, data_dir)
        
        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f'Data directory not found: {data_dir}'))
            return
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            ProductImage.objects.all().delete()
            ProductVariant.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            Brand.objects.all().delete()
        
        with transaction.atomic():
            # Import brands
            self.stdout.write('Importing brands...')
            brands = {}
            brands_file = os.path.join(data_dir, 'brands.csv')
            if os.path.exists(brands_file):
                with open(brands_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        brand, created = Brand.objects.get_or_create(
                            id=int(row['brand_id']),
                            defaults={
                                'name': row['name'],
                                'country': row['country'],
                            }
                        )
                        brands[int(row['brand_id'])] = brand
                        if created:
                            self.stdout.write(f'  Created brand: {brand.name}')
            else:
                self.stdout.write(self.style.WARNING(f'  brands.csv not found at {brands_file}'))
            
            # Import categories
            self.stdout.write('Importing categories...')
            categories = {}
            categories_file = os.path.join(data_dir, 'categories.csv')
            if os.path.exists(categories_file):
                with open(categories_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        parent = None
                        if row.get('parent_category_id') and row['parent_category_id'].strip():
                            parent_id = int(row['parent_category_id'])
                            if parent_id in categories:
                                parent = categories[parent_id]
                        
                        category, created = Category.objects.get_or_create(
                            id=int(row['category_id']),
                            defaults={
                                'name': row['name'],
                                'slug': row['slug'],
                                'parent': parent,
                            }
                        )
                        categories[int(row['category_id'])] = category
                        if created:
                            self.stdout.write(f'  Created category: {category.name}')
            else:
                self.stdout.write(self.style.WARNING(f'  categories.csv not found at {categories_file}'))
            
            # Import products
            self.stdout.write('Importing products...')
            products = {}
            products_file = os.path.join(data_dir, 'products.csv')
            if os.path.exists(products_file):
                with open(products_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        brand_id = int(row['brand_id'])
                        category_id = int(row['category_id'])
                        
                        if brand_id not in brands:
                            self.stdout.write(self.style.WARNING(f'  Brand {brand_id} not found for product {row["product_id"]}'))
                            continue
                        if category_id not in categories:
                            self.stdout.write(self.style.WARNING(f'  Category {category_id} not found for product {row["product_id"]}'))
                            continue
                        
                        slug = (row.get('slug') or '').strip() or slugify(row['name']) or f"product-{row['product_id']}"
                        product, created = Product.objects.get_or_create(
                            id=int(row['product_id']),
                            defaults={
                                'name': row['name'],
                                'slug': slug,
                                'description': row['description'],
                                'brand': brands[brand_id],
                                'category': categories[category_id],
                                'material_summary': row.get('material_summary', ''),
                                'care_summary': row.get('care_summary', ''),
                            }
                        )
                        products[int(row['product_id'])] = product
                        if created:
                            self.stdout.write(f'  Created product: {product.name}')
            else:
                self.stdout.write(self.style.WARNING(f'  products.csv not found at {products_file}'))
            
            # Import product variants
            self.stdout.write('Importing product variants...')
            variants = {}
            variants_file = os.path.join(data_dir, 'product_variants.csv')
            if os.path.exists(variants_file):
                with open(variants_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        product_id = int(row['product_id'])
                        
                        if product_id not in products:
                            self.stdout.write(self.style.WARNING(f'  Product {product_id} not found for variant {row["variant_id"]}'))
                            continue
                        
                        variant, created = ProductVariant.objects.get_or_create(
                            id=int(row['variant_id']),
                            defaults={
                                'product': products[product_id],
                                'size': row['size'],
                                'color': row['color'],
                                'sku': row['sku'],
                                'price': float(row['price']),
                                'stock_qty': int(row['stock_qty']),
                                'weight_g': int(row['weight_g']) if row.get('weight_g') else None,
                            }
                        )
                        variants[int(row['variant_id'])] = variant
                        if created:
                            self.stdout.write(f'  Created variant: {variant.product.name} - {variant.size} - {variant.color}')
            else:
                self.stdout.write(self.style.WARNING(f'  product_variants.csv not found at {variants_file}'))
            
            # Import product images
            self.stdout.write('Importing product images...')
            images_file = os.path.join(data_dir, 'product_images_placeholder.csv')
            if os.path.exists(images_file):
                with open(images_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        product_id = int(row['product_id']) if row.get('product_id') else None
                        variant_id = int(row['variant_id']) if row.get('variant_id') and row['variant_id'].strip() else None
                        
                        if product_id and product_id not in products:
                            continue
                        if variant_id and variant_id not in variants:
                            variant_id = None
                        
                        ProductImage.objects.get_or_create(
                            id=int(row['image_id']),
                            defaults={
                                'product': products[product_id] if product_id else None,
                                'variant': variants[variant_id] if variant_id else None,
                                'image_url': row['image_url'],
                                'alt_text': row.get('alt_text', ''),
                                'sort_order': int(row.get('sort_order', 0)),
                            }
                        )
                self.stdout.write('  Product images imported')
            else:
                self.stdout.write(self.style.WARNING(f'  product_images_placeholder.csv not found at {images_file}'))
        
        self.stdout.write(self.style.SUCCESS('Data import completed!'))
        self.stdout.write(f'  Brands: {Brand.objects.count()}')
        self.stdout.write(f'  Categories: {Category.objects.count()}')
        self.stdout.write(f'  Products: {Product.objects.count()}')
        self.stdout.write(f'  Variants: {ProductVariant.objects.count()}')
        self.stdout.write(f'  Images: {ProductImage.objects.count()}')
