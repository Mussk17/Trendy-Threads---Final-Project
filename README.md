# Trendy Threads Ecommerce Site

A complete Django-based fashion ecommerce site with Stripe payments and AWS Bedrock RAG chatbot support.

## Tech Stack

- **Backend:** Django 5.x, Python 3.x
- **Database:** SQLite (development), PostgreSQL recommended for production
- **Payments:** Stripe (test mode)
- **AI/RAG:** AWS Bedrock Knowledge Base (Claude)
- **Frontend:** HTML, CSS, JavaScript (Bootstrap 5, HTMX)
- **Dependencies:** django-environ, stripe, boto3, Pillow, pandas

## Features

- **Product Management**: Products with variants (size/color combinations), brands, categories
- **Shopping Cart**: Session-based cart with variant selection
- **Stripe Payments**: Checkout via Stripe Checkout (redirect to Stripe’s page for card, Apple Pay, Google Pay; orders via webhook)
- **AWS Bedrock RAG Chatbot**: Support chatbot using AWS Bedrock Knowledge Base
- **Modern UI**: Clean, responsive design optimized for fashion ecommerce

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:

- `SECRET_KEY` – Django secret key  
- `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY` – from [Stripe Dashboard](https://dashboard.stripe.com/apikeys)  
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `BEDROCK_KNOWLEDGE_BASE_ID` – for the RAG chatbot

Never commit `.env`. It is listed in `.gitignore`.

### 3. Setup Database

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Import product data from CSV files
python manage.py import_ecommerce_data
```

The import command looks for CSV files in `data/seed_data/` (within the project) by default. The seed data is included in the project for easy setup.

To use a different directory:

```bash
python manage.py import_ecommerce_data --data-dir /path/to/csv/files
```

Use `--clear` to clear existing data before importing:

```bash
python manage.py import_ecommerce_data --clear
```

### 4. Run Server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000

## Project Structure

- `config/` - Django settings and URL configuration
- `products/` - Product models, views, admin, CSV import command
- `cart/` - Session-based shopping cart
- `orders/` - Order models, Stripe checkout integration
- `chatbot/` - AWS Bedrock RAG chatbot service
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)

## Database Models

- **Brand**: Brand name and country
- **Category**: Hierarchical categories (supports parent categories)
- **Product**: Product information with brand and category relationships
- **ProductVariant**: Size/color combinations with individual prices and stock
- **ProductImage**: Multiple images per product/variant
- **Order**: Order information with Stripe payment details
- **OrderItem**: Order line items with variant information

## Stripe Setup

1. Get test keys from [Stripe Dashboard](https://dashboard.stripe.com/apikeys) (Test mode)
2. Add `STRIPE_PUBLISHABLE_KEY` (pk_test_...) and `STRIPE_SECRET_KEY` (sk_test_...) to `.env`
3. **Webhooks (required for Stripe Checkout):** So orders are created even if the customer closes the tab after paying, add `STRIPE_WEBHOOK_SECRET` to `.env`
4. **Optional:** `DOMAIN` – base URL for success/cancel redirects (default: `http://localhost:8000`)

**Payment flow (Stripe Checkout only, ideal for demos):** Click "Pay with Stripe Checkout" → redirect to Stripe’s hosted page (card, Apple Pay, Google Pay) → order created via webhook. Works even if the user closes the tab after paying.

**Local testing (with webhook):**
```bash
# Terminal 1: Run Django
python manage.py runserver

# Terminal 2: Forward webhooks (install Stripe CLI first)
stripe listen --forward-to localhost:8000/orders/webhook/
```
Copy the `whsec_...` signing secret from the Stripe CLI output into `.env` as `STRIPE_WEBHOOK_SECRET`.

**Test Cards:**
- Success: `4242 4242 4242 4242`
- Declined: `4000 0000 0000 0002`
- Use any future expiry, any 3-digit CVC, any ZIP

### Step-by-step: Dummy test (local)

**Prerequisites:** `.env` has `STRIPE_PUBLISHABLE_KEY` and `STRIPE_SECRET_KEY` (test keys). For webhook tests, you need Stripe CLI and `STRIPE_WEBHOOK_SECRET` in `.env`.

1. **Start the app**
   ```bash
   cd trendy-threads
   python manage.py runserver
   ```
   Leave this running.

2. **Add something to the cart**
   - Open http://127.0.0.1:8000/
   - Go to Shop, add a product to cart, then open http://127.0.0.1:8000/orders/checkout/

3. **Test Stripe Checkout (redirect flow)**
   - On the checkout page, click **"Pay $X with Stripe Checkout"** (purple button).
   - You are redirected to Stripe’s page. Use:
     - Card: `4242 4242 4242 4242`
     - Expiry: any future date (e.g. 12/34)
     - CVC: any 3 digits (e.g. 123)
     - ZIP: any (e.g. 12345)
   - Complete payment. You should land on `/orders/success/` with “Payment successful”.
   - In Django admin (http://127.0.0.1:8000/admin/orders/order/) confirm a new order with status “Paid” and `paid_at` set.

4. **Test webhook (order created even if tab is closed)** (optional)
   - In a **second terminal**: `stripe listen --forward-to localhost:8000/orders/webhook/`. Copy the `whsec_...` secret to `.env` as `STRIPE_WEBHOOK_SECRET`, then restart `runserver`.
   - Add to cart, go to checkout, click **"Pay with Stripe Checkout"**, complete payment on Stripe, then **close the success tab** before the redirect finishes.
   - In admin, the order should still appear via the `checkout.session.completed` webhook.

5. **Test cancel**
   - Checkout → “Pay with Stripe Checkout” → on Stripe’s page click **Back** (or cancel). You should land on `/orders/cancel/` and no order should be created.

6. **Test declined card (optional)**
   - Use card `4000 0000 0000 0002`. Payment should be declined; no order in admin.

## AWS Bedrock RAG Chatbot Setup

1. Create IAM user with `AmazonBedrockFullAccess` and `AmazonS3FullAccess`
2. Create S3 bucket and upload knowledge base files from `Database/academic_ecommerce_rag_pack_txt/knowledge_base/`
3. Create Bedrock Knowledge Base:
   - Data source: Your S3 bucket
   - Use default embeddings and "Quick create" vector store
   - Sync and wait until Ready
4. Copy Knowledge Base ID to `BEDROCK_KNOWLEDGE_BASE_ID` in `.env`
5. Add AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`) to `.env`

## Admin Interface

Access admin at http://127.0.0.1:8000/admin/

Manage:
- Brands
- Categories (hierarchical)
- Products (with inline variants and images)
- Orders

## CSV Import

The `import_ecommerce_data` command imports data from `data/seed_data/`:
- `brands.csv` → Brand model (2 brands)
- `categories.csv` → Category model (3 categories with hierarchical support)
- `products.csv` → Product model (15 products)
- `product_variants.csv` → ProductVariant model (~193 variants with individual prices/stock)
- `product_images_placeholder.csv` → ProductImage model (~32 images)

See `data/README.md` for detailed information about the seed data structure.

## Key URLs

- Home: http://127.0.0.1:8000/
- Shop: http://127.0.0.1:8000/products/
- Cart: http://127.0.0.1:8000/cart/
- Checkout: http://127.0.0.1:8000/orders/checkout/
- Admin: http://127.0.0.1:8000/admin/

## Stripe Checkout – Local Verification Checklist

1. [ ] Add items to cart and go to `/orders/checkout/`
2. [ ] Click **"Pay $X with Stripe Checkout"** (purple button)
3. [ ] Browser redirects to Stripe; enter card `4242 4242 4242 4242`, any future expiry, any CVC
4. [ ] Complete payment → redirected to `/orders/success/`; see "Payment successful" and order total
5. [ ] In Django admin (`/admin/orders/order/`), confirm order exists with `status=Paid` and `paid_at` set
6. [ ] **Webhook test (user closed tab):** Start `stripe listen --forward-to localhost:8000/orders/webhook/`, pay again, close the Stripe success tab before it redirects. Order should still appear in admin via webhook.
7. [ ] Test cancel: click "Pay with Stripe Checkout", then click "Back" on Stripe → lands on `/orders/cancel/`

## Production Checklist

- [ ] Set `DEBUG=False` and strong `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Use Stripe **live** keys and HTTPS
- [ ] Serve over HTTPS
- [ ] Keep `.env` secure (use secrets manager in production)
- [ ] Run `python manage.py collectstatic` for static files
- [ ] Consider PostgreSQL instead of SQLite for production

## Running Tests

```bash
python manage.py test accounts cart orders chatbot
```

Tests cover authentication flows (including open redirect prevention), cart validation, checkout redirects, and chatbot input handling.

## Security Considerations

- **Secrets:** All API keys and secrets are read from environment variables via `.env` (never committed).
- **CSRF:** Enabled on all state-changing endpoints; Stripe webhook uses signature verification instead.
- **Headers:** X-Frame-Options, X-Content-Type-Options, and X-XSS-Protection are set.
- **Input validation:** Cart quantities, payment IDs, and chatbot input are validated server-side.
- **Open redirects:** Login `next` parameter is validated before redirect.

## Privacy

- Personal data is collected only when necessary (registration, checkout).
- Passwords are hashed; no raw credentials are logged.
- Payment details are handled by Stripe; card data never touches the server.
- Chatbot queries are sent to AWS Bedrock; no persistent storage of chat content.

## License

This project is for educational purposes.
