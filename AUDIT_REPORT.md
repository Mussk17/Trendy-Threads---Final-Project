# Audit Report — Trendy Threads E-Commerce Project

**Date:** February 2026  
**Scope:** Full-stack e-commerce web application (Django, Stripe, AWS Bedrock RAG)  
**Purpose:** Academic portfolio / demonstration project

---

## 1. Issues Found Report


---



## 4. Testing Guide


---

## 5. Security and Privacy Checklist

| Area | Status |
|------|--------|
| Secrets in environment variables | Done |
| `.env` in `.gitignore` | Done |
| `.env.example` with placeholders | Done |
| Stripe webhook signature verification | Done (existing) |
| Webhook idempotency (order creation) | Done (existing) |
| Server-side price validation (cart/checkout) | Done (existing) |
| Login open redirect prevention | Done |
| CSRF on state-changing views | Done (existing) |
| X-Frame-Options, X-Content-Type-Nosniff | Done |
| Input validation (cart, chatbot, payment intent) | Done |
| AWS credentials from environment | Done (existing) |
| No sensitive data in logs | Done (no passwords, payment details, API keys) |
| Password hashing (Django default) | Done (existing) |
| Session security | Done (Django defaults) |

### Privacy

- Data minimization: only registration and checkout collect PII.
- Passwords hashed via Django; no raw credentials logged.
- Payment data handled by Stripe; card data not processed server-side.
- Chatbot queries sent to Bedrock; no persistent storage of chat content.
- README updated with privacy approach.

---

## 6. Threat Model Summary

### Assets

- User credentials and profile data
- Payment intent/session identifiers
- Order records
- Application logic (cart, checkout, chatbot)

### Attack Surfaces

- Authentication (login, registration)
- Cart (add, update, remove)
- Checkout and Stripe webhook
- Chatbot API
- Admin

### Threats and Mitigations

| Threat | Mitigation |
|--------|------------|
| Open redirect after login | `url_has_allowed_host_and_scheme` validation |
| Client-side cart manipulation | Server-side quantity and price validation |
| Price tampering | Stripe and cart use server-side prices |
| Webhook spoofing | Stripe signature verification |
| Duplicate orders from webhook retries | Idempotency checks on `stripe_session_id` / `stripe_payment_intent_id` |
| Chatbot prompt injection | Input length limit, control-char stripping, RAG prompt constraints |
| Bedrock API abuse | Timeout, retry, sanitized input |
| Sensitive data exposure | Generic error messages, no secrets in logs |

---

## 7. Code Organization Map

```
trendy-threads/
├── config/           # Django settings, URLs
├── accounts/         # Auth, profile, addresses
├── products/         # Catalog, search, wishlist
├── cart/             # Session cart, line items
├── orders/           # Checkout, Stripe, webhook
├── chatbot/          # Bedrock RAG service and API
├── templates/        # HTML (base, products, cart, orders, chatbot)
├── static/           # CSS, JS, images
├── data/             # Seed data
└── .env.example      # Environment template
```

- **Views:** Request handling and orchestration
- **Models:** Data layer and business objects
- **Services:** `chatbot/services.py` — Bedrock RAG logic
- **Forms:** `accounts/forms.py` — user and address forms
- **Context processors:** Cart and nav data for templates

---

## 8. Remaining Considerations

- **Rate limiting:** Not implemented; consider for auth and chatbot in production.
- **CSP:** Content-Security-Policy not configured; evaluate if stricter CSP is needed.
- **Database:** SQLite used for development; PostgreSQL recommended for production.
- **Static files:** Use `collectstatic` and a static file server in production.
- **Environment:** Rotate any exposed credentials from `.env` if the file was ever committed or shared.
