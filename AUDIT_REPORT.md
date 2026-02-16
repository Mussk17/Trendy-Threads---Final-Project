# Audit Report — Trendy Threads E-Commerce Project

**Date:** February 2026  
**Scope:** Full-stack e-commerce web application (Django, Stripe, AWS Bedrock RAG)  
**Purpose:** Academic portfolio / demonstration project

---

## 1. Issues Found Report

### Critical
| ID | Issue | Location | Severity |
|----|-------|----------|----------|
| C1 | Login open redirect — `next` parameter not validated, allowing redirect to arbitrary URLs | `accounts/views.py` | Critical |
| C2 | Real API keys and secrets present in `.env` — risk if `.env` is committed or shared | `.env` | Critical |

### High
| ID | Issue | Location | Severity |
|----|-------|----------|----------|
| H1 | Cart add accepts negative quantities — can lead to negative cart totals | `cart/views.py`, `cart/cart.py` | High |
| H2 | `update_payment_intent` exposes raw Stripe error messages to client | `orders/views.py` | High |
| H3 | Bedrock API calls lack timeout and retry logic | `chatbot/services.py` | High |

### Medium
| ID | Issue | Location | Severity |
|----|-------|----------|----------|
| M1 | No input length limit or sanitization for chatbot questions | `chatbot/services.py` | Medium |
| M2 | Missing security headers (X-Frame-Options, X-Content-Type-Nosniff) | `config/settings.py` | Medium |
| M3 | Insufficient structured logging for payment and auth events | Various | Medium |
| M4 | Cart update quantity could be invalid (ValueError on non-numeric input) | `cart/views.py` | Medium |

### Low
| ID | Issue | Location | Severity |
|----|-------|----------|----------|
| L1 | No `.env.example` for onboarding | Project root | Low |
| L2 | Minimal test coverage | `accounts/tests.py`, etc. | Low |
| L3 | README lacked security and testing documentation | `README.md` | Low |

---

## 2. Fixes Applied Report

| Fix | Issue Addressed | Files Modified | Rationale |
|-----|-----------------|----------------|-----------|
| Open redirect prevention | C1 | `accounts/views.py` | Use `url_has_allowed_host_and_scheme` to validate `next` before redirect; reject external absolute URLs |
| `.env.example` created | C2, L1 | `.env.example` | Provides a template with placeholder values; `.env` remains gitignored |
| Cart quantity validation | H1 | `cart/views.py`, `cart/cart.py` | Enforce `quantity >= 1` in add; validate quantity in update with try/except and `max(0, int(...))` |
| Payment intent error handling | H2 | `orders/views.py` | Return generic error messages; validate `payment_intent_id` format (`pi_` prefix); cap email length |
| Bedrock timeout and retry | H3 | `chatbot/services.py` | Add `Config` with `read_timeout=30`, `connect_timeout=10`, and retries (2 attempts, standard mode) |
| Chatbot input sanitization | M1 | `chatbot/services.py` | Limit length to 1000 chars; strip control characters; validate before calling Bedrock |
| Security headers | M2 | `config/settings.py` | Set `X_FRAME_OPTIONS`, `SECURE_BROWSER_XSS_FILTER`, `SECURE_CONTENT_TYPE_NOSNIFF` |
| Structured logging | M3 | `config/settings.py`, `orders/views.py`, `chatbot/services.py` | Add LOGGING config; log webhook events (without sensitive data); use `logger.warning` for Bedrock failures |
| Cart update validation | M4 | `cart/views.py` | Wrap quantity parsing in try/except and use `max(0, int(...))` |
| Test coverage | L2 | `accounts/tests.py`, `cart/tests.py`, `orders/tests.py`, `chatbot/tests.py` | Add tests for registration, open redirect prevention, cart quantity validation, checkout redirect, chatbot empty input |
| README updates | L3 | `README.md` | Add tech stack, `.env.example` setup, test instructions, security considerations, and privacy approach |

### Verification

- **Open redirect:** `test_login_open_redirect_prevented` confirms redirect to `products:home` when `next=https://evil.com`.
- **Cart quantity:** `test_cart_add_validates_quantity` confirms negative quantity becomes 1.
- **Checkout empty cart:** `test_checkout_redirects_empty_cart` confirms redirect to cart.
- **Chatbot empty input:** `test_chat_rejects_empty_question` confirms 400 for empty message.

---

## 3. Files Changed Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `.env.example` | Created | Template for environment variables with placeholders |
| `accounts/views.py` | Modified | Open redirect prevention for login `next` parameter |
| `accounts/tests.py` | Modified | Tests for registration and open redirect prevention |
| `cart/cart.py` | Modified | Quantity validation in `add` |
| `cart/views.py` | Modified | Quantity validation in add and update |
| `cart/tests.py` | Created | Test for cart add quantity validation |
| `chatbot/services.py` | Modified | Input sanitization, timeout, retry, logging |
| `chatbot/tests.py` | Created | Test for empty question rejection |
| `chatbot/views.py` | Modified | CSRF exempt retained for read-only API |
| `config/settings.py` | Modified | Security headers, logging configuration |
| `orders/views.py` | Modified | Logging, error handling, PaymentIntent validation |
| `orders/tests.py` | Created | Test for checkout empty-cart redirect |
| `README.md` | Modified | Tech stack, setup, tests, security, privacy |

---

## 4. Testing Guide

### Run All Tests

```bash
cd trendy-threads
python manage.py test accounts cart orders chatbot
```

### Critical Change Tests

**1. Login open redirect**

- Log in with `?next=https://evil.com`.
- Expect redirect to `products:home`, not to external site.

**2. Cart quantity validation**

- POST to `/cart/add/<variant_id>/` with `quantity=-5`.
- Cart quantity should be 1.

**3. Checkout empty cart**

- GET `/orders/checkout/` with empty cart.
- Expect redirect to `/cart/`.

**4. Chatbot empty input**

- POST to `/chatbot/api/chat/` with `{"message": ""}`.
- Expect 400 with a reply indicating invalid input.

**5. Stripe webhook**

- Use Stripe CLI: `stripe listen --forward-to localhost:8000/orders/webhook/`
- Trigger `checkout.session.completed` event.
- Confirm order in admin and webhook processing in logs.

**6. Bedrock chatbot**

- Send a valid question via the Support widget.
- Confirm response and sources.
- Send a very long string (>1000 chars) — expect truncation.

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
