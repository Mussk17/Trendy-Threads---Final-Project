# Audit Report – Trendy Threads E-Commerce Project  

**Date:** February 2026  
**Project:** Trendy Threads (Django E-Commerce with Stripe & AWS Bedrock RAG Chatbot)  
**Purpose:** Final Year Project Documentation  

---

## Introduction  

This audit report gives an overview of the security, structure, and overall implementation of the Trendy Threads e-commerce web application.  

The goal of this document is to show that the project was developed with security and best practices in mind. Since this is a final-year academic project, the focus is on demonstrating understanding of real-world development standards, especially in areas like payments, authentication, and AI integration.

---

## Project Overview  

Trendy Threads is a full-stack Django-based fashion e-commerce website. It includes:

- User registration and login  
- Product listing with size and color variants  
- Session-based shopping cart  
- Secure payments using Stripe Checkout  
- AI-powered chatbot using AWS Bedrock (RAG architecture)  

The project is divided into different Django apps:

accounts/   → Authentication and profiles  
products/   → Product catalog and variants  
cart/       → Cart functionality  
orders/     → Checkout and Stripe integration  
chatbot/    → AWS Bedrock RAG logic  
config/     → Project settings  


I structured the project this way to keep responsibilities separate and make the code easier to manage and understand.

---

## Security Review  

Since this is an e-commerce system, security was one of the main considerations during development.

### 1️⃣ Environment Variables & Secrets  

All sensitive information such as:

- Django secret key  
- Stripe API keys  
- AWS credentials  

are stored in a `.env` file and loaded using environment variables.

- `.env` is included in `.gitignore`
- `.env.example` is provided with placeholder values  

This prevents sensitive data from being exposed in the GitHub repository.

### 2️⃣ Authentication Security  

- Passwords are securely hashed using Django’s built-in system.
- I added validation to prevent open redirect attacks during login.
- Django’s default session management is used.

**Password hashing** means passwords are not stored in plain text. Instead, they are converted into a secure format that cannot easily be reversed.

### 3️⃣ Stripe Payment Security  

Stripe Checkout is used for payments. This means:

- Users enter card details on Stripe’s secure hosted page.
- The application never stores or processes card data directly.

This significantly reduces security risks.

#### Webhook Protection  

Stripe sends a webhook to confirm successful payment.

The system includes:

- Signature verification to ensure the request is from Stripe.
- Idempotency checks to prevent duplicate orders if Stripe retries the webhook.

**Idempotency** means the same event will not create multiple orders even if processed more than once.

### 4️⃣ Server-Side Validation  

The system does not trust client-side data.

For example:

- Cart quantities are validated on the server.
- Prices are calculated server-side.
- Checkout totals are verified before payment.
- Chatbot input has length limits and basic sanitization.

This prevents manipulation through browser tools.

### 5️⃣ CSRF & Security Headers  

The application includes:

- CSRF protection for forms  
- X-Frame-Options  
- X-Content-Type-Options  

**CSRF (Cross-Site Request Forgery)** is when a malicious site tries to make a user perform actions without their permission. Django provides built-in protection for this.

---

## AI & Cloud Integration  

The chatbot uses AWS Bedrock with Retrieval-Augmented Generation (RAG).

### How it works:

1. Knowledge documents are uploaded to an Amazon S3 bucket.
2. AWS Bedrock creates a Knowledge Base from those documents.
3. When a user asks a question:
   - Relevant information is retrieved.
   - The Claude model generates a contextual response.

**RAG (Retrieval-Augmented Generation)** means the AI first retrieves relevant information before generating a response. This improves accuracy and reduces incorrect answers.

Security considerations:

- AWS credentials are stored in environment variables.
- Chatbot inputs are sanitized.
- Chat conversations are not permanently stored.

---

## Threat Model (Basic Overview)  

### Main Assets  

- User credentials  
- Order records  
- Payment session IDs  
- Application logic  

### Possible Risks  

- Login manipulation  
- Cart price tampering  
- Fake webhook calls  
- Chatbot misuse  

### Mitigations Implemented  

| Risk | Protection |
|------|------------|
| Open redirect | URL validation |
| Price tampering | Server-side price validation |
| Fake webhook | Stripe signature verification |
| Duplicate orders | Idempotency checks |
| Prompt injection | Input sanitization |

---

## Database & Data Handling  

The project uses:

- SQLite for development  
- PostgreSQL/Aurora (recommended for production)

Main relational models include:

- Brand  
- Category (hierarchical)  
- Product  
- ProductVariant  
- Order  
- OrderItem  

For AI functionality:

- Knowledge documents are stored in Amazon S3.
- AWS Bedrock manages vector indexing separately from the main database.

This shows understanding of both traditional relational databases and modern cloud-based knowledge systems.

---

## Production Considerations  

If deployed to production, the following should be done:

- Set `DEBUG = False`
- Use PostgreSQL
- Enable HTTPS
- Rotate and secure credentials
- Run `collectstatic`
- Consider adding rate limiting
- Add Content Security Policy (CSP)

These improvements would make the system more secure for real-world usage.

---

## Final Reflection  

Overall, this project demonstrates:

- Secure authentication practices  
- Proper Stripe payment integration  
- Secure webhook handling  
- Use of environment variables  
- Integration of AWS Bedrock RAG chatbot  
- Basic threat modeling awareness  

While it is an academic project, I aimed to follow industry-level best practices wherever possible. The system is structured, secure at a fundamental level, and demonstrates practical understanding of modern e-commerce and AI-based web applications.
