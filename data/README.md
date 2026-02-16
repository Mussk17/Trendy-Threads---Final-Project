# Seed Data for Trendy Threads

This folder contains seed data for populating the Trendy Threads ecommerce database.

## Structure

```
data/
├── seed_data/
│   ├── brands.csv              # Brand information
│   ├── categories.csv          # Product categories (hierarchical)
│   ├── products.csv            # Product information
│   ├── product_variants.csv   # Size/color variants with prices and stock
│   └── product_images_placeholder.csv  # Product images
└── README.md                   # This file
```

## Data Files

### brands.csv
Contains brand information:
- `brand_id`: Unique brand identifier
- `name`: Brand name
- `country`: Country of origin

**Example:** North & Nook (UK), Cedar Studio (UK)

### categories.csv
Contains product categories with hierarchical support:
- `category_id`: Unique category identifier
- `name`: Category name
- `slug`: URL-friendly category name
- `parent_category_id`: Optional parent category ID for hierarchical structure

**Categories:** Tops, Bottoms, Outerwear

### products.csv
Contains product information:
- `product_id`: Unique product identifier
- `name`: Product name
- `slug`: URL-friendly product name
- `description`: Product description
- `brand_id`: Foreign key to brands.csv
- `category_id`: Foreign key to categories.csv
- `material_summary`: Material composition
- `care_summary`: Care instructions

**Products:** 15 fashion items including tees, shirts, jeans, jackets, coats, etc.

### product_variants.csv
Contains size/color combinations for each product:
- `variant_id`: Unique variant identifier
- `product_id`: Foreign key to products.csv
- `size`: Size (XS, S, M, L, XL)
- `color`: Color name
- `sku`: Stock keeping unit code
- `price`: Price for this specific variant (can vary by size)
- `stock_qty`: Available stock quantity
- `weight_g`: Weight in grams

**Variants:** ~193 variants across all products

**Key Feature:** Each variant has its own price and stock, allowing for flexible pricing (e.g., XL might cost more than S).

### product_images_placeholder.csv
Contains image references for products:
- `image_id`: Unique image identifier
- `product_id`: Foreign key to products.csv
- `variant_id`: Optional foreign key to product_variants.csv
- `image_url`: Path to image file
- `alt_text`: Alternative text for accessibility
- `sort_order`: Display order

**Images:** ~32 images (2 per product typically)

## Usage

Import this data into your Django database using:

```bash
python manage.py import_ecommerce_data
```

This will import all CSV files from `data/seed_data/` by default.

To use a different directory:

```bash
python manage.py import_ecommerce_data --data-dir /path/to/csv/files
```

To clear existing data before importing:

```bash
python manage.py import_ecommerce_data --clear
```

## Data Statistics

After import, you should have:
- **2 brands**
- **3 categories**
- **15 products**
- **~193 product variants** (size/color combinations)
- **~32 product images**

## Notes

- Image URLs point to `/static/images/products/`. After importing, create placeholder images by running from project root: `python scripts/create_product_placeholders.py` (requires Pillow). Or add your own product photos with the same filenames.
- Variant prices can differ by size (e.g., L and XL may cost more than S)
- Stock quantities are realistic sample data
- All data is designed for a fashion ecommerce site
