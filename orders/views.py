import logging
import stripe
from decimal import Decimal
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from cart.cart import Cart
from .models import Order, OrderItem
from products.models import ProductVariant

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


def _metadata_items_from_cart(cart):
    """Build metadata 'items' string: variant_id:qty,variant_id:qty for webhook order creation."""
    return ','.join(f"{vid}:{item['quantity']}" for vid, item in cart.cart.items())


def _create_order_from_payment_intent_metadata(intent):
    """
    Persist order confirmation to the database from a succeeded PaymentIntent (e.g. webhook).
    Idempotency: if an order already exists for this payment_intent id, we skip (no duplicate orders).
    Used when the customer never hits the success page (e.g. closed tab after paying).
    """
    pid = intent.id
    if Order.objects.filter(stripe_payment_intent_id=pid).exists():
        return
    metadata = intent.metadata or {}
    email = (metadata.get('email') or '').strip() or 'guest@example.com'
    total = Decimal(intent.amount / 100)
    items_str = (metadata.get('items') or '').strip()
    if not items_str:
        return
    # Parse "variant_id:qty,variant_id:qty"
    pairs = []
    for part in items_str.split(','):
        part = part.strip()
        if ':' in part:
            vid, qty = part.split(':', 1)
            try:
                pairs.append((vid.strip(), int(qty.strip()) or 0))
            except (ValueError, TypeError):
                continue
    if not pairs:
        return
    variant_ids = [vid for vid, qty in pairs if qty > 0]
    variants = ProductVariant.objects.filter(id__in=variant_ids).select_related('product')
    variant_map = {str(v.id): v for v in variants}
    order = Order.objects.create(
        stripe_session_id='',
        stripe_payment_intent_id=pid,
        user=None,
        email=email,
        first_name='',
        last_name='',
        address_line1='',
        address_line2='',
        city='',
        state='',
        postal_code='',
        total=total,
        status='paid',
        paid_at=timezone.now(),
    )
    for variant_id, qty in pairs:
        if qty <= 0 or variant_id not in variant_map:
            continue
        variant = variant_map[variant_id]
        OrderItem.objects.create(
            order=order,
            product_name=variant.product.name,
            product_id=variant.product.id,
            variant_id=variant.id,
            size=variant.size,
            color=variant.color,
            quantity=qty,
            price=variant.price,
        )


def _create_order_from_cart(cart, email='', stripe_payment_intent_id='', stripe_session_id='', total=None, user=None):
    """
    Persist order confirmation to the database: create Order and OrderItems from cart.
    Idempotency: we never create a second order for the same payment. If an order already
    exists for this stripe_payment_intent_id or stripe_session_id, we skip creation.
    """
    if stripe_payment_intent_id and Order.objects.filter(stripe_payment_intent_id=stripe_payment_intent_id).exists():
        return
    if stripe_session_id and Order.objects.filter(stripe_session_id=stripe_session_id).exists():
        return
    order_total = total if total is not None else cart.get_total_price()
    order = Order.objects.create(
        stripe_session_id=stripe_session_id or '',
        stripe_payment_intent_id=stripe_payment_intent_id or '',
        user=user,
        email=email or (user.email if user and user.email else 'guest@example.com'),
        first_name='',
        last_name='',
        address_line1='',
        address_line2='',
        city='',
        state='',
        postal_code='',
        total=order_total,
        status='paid',
        paid_at=timezone.now(),
    )
    
    # Create order items from cart variants
    variant_ids = list(cart.cart.keys())
    variants = ProductVariant.objects.filter(id__in=variant_ids).select_related('product')
    variant_map = {str(v.id): v for v in variants}
    
    for variant_id, item in cart.cart.items():
        if variant_id in variant_map:
            variant = variant_map[variant_id]
            OrderItem.objects.create(
                order=order,
                product_name=variant.product.name,
                product_id=variant.product.id,
                variant_id=variant.id,
                size=variant.size,
                color=variant.color,
                quantity=item['quantity'],
                price=variant.price,
            )
    cart.clear()


def _create_order_from_checkout_session(session):
    """
    Create or update order from Stripe Checkout Session (webhook).
    Used when customer pays via Stripe Checkout - works even if they close the tab before
    reaching the success page. Idempotent: no duplicate orders for same session_id.
    """
    session_id = session.get('id') or session.id
    if not session_id:
        return
    # Already have order? Just ensure it's marked paid (in case success page created it first)
    existing = Order.objects.filter(stripe_session_id=session_id).first()
    payment_intent_id = ''
    if session.get('payment_intent'):
        payment_intent_id = session['payment_intent'] if isinstance(session['payment_intent'], str) else session['payment_intent'].id
    if existing:
        existing.status = 'paid'
        existing.paid_at = timezone.now()
        if payment_intent_id:
            existing.stripe_payment_intent_id = payment_intent_id
        existing.save()
        return
    # Create new order from session metadata
    metadata = session.get('metadata') or {}
    items_str = (metadata.get('items') or '').strip()
    if not items_str:
        return
    email = (session.get('customer_email') or '') or ((session.get('customer_details') or {}).get('email') or '') or 'guest@example.com'
    total = Decimal((session.get('amount_total') or 0) / 100)
    # Parse "variant_id:qty,variant_id:qty"
    pairs = []
    for part in items_str.split(','):
        part = str(part).strip()
        if ':' in part:
            vid, qty = part.split(':', 1)
            try:
                pairs.append((vid.strip(), int(qty.strip()) or 0))
            except (ValueError, TypeError):
                continue
    if not pairs:
        return
    variant_ids = [vid for vid, qty in pairs if qty > 0]
    variants = ProductVariant.objects.filter(id__in=variant_ids).select_related('product')
    variant_map = {str(v.id): v for v in variants}
    order = Order.objects.create(
        stripe_session_id=session_id,
        stripe_payment_intent_id=payment_intent_id or '',
        user=None,
        email=email,
        first_name='',
        last_name='',
        address_line1='',
        address_line2='',
        city='',
        state='',
        postal_code='',
        total=total,
        status='paid',
        paid_at=timezone.now(),
    )
    for variant_id, qty in pairs:
        if qty <= 0 or variant_id not in variant_map:
            continue
        variant = variant_map[variant_id]
        OrderItem.objects.create(
            order=order,
            product_name=variant.product.name,
            product_id=variant.product.id,
            variant_id=variant.id,
            size=variant.size,
            color=variant.color,
            quantity=qty,
            price=variant.price,
        )


@require_http_methods(['GET'])
def checkout(request):
    """
    Checkout page: on-site credit card form. PaymentIntent created on load for secure card entry.
    No redirect; no third-party branding shown to the user.
    """
    cart = Cart(request)
    if not cart.cart:
        return redirect('cart:cart_detail')
    pk = settings.STRIPE_PUBLISHABLE_KEY or ''
    context = {
        'cart': cart,
        'stripe_publishable_key': pk,
        'client_secret': None,
        'payment_intent_id': None,
    }
    if not settings.STRIPE_SECRET_KEY:
        return render(request, 'orders/checkout.html', context)
    total = cart.get_total_price()
    amount_cents = int(total * 100)
    if amount_cents < 50:
        return redirect('cart:cart_detail')
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='usd',
            payment_method_types=['card'],
            metadata={
                'email': '',
                'items': _metadata_items_from_cart(cart),
            },
        )
        context['client_secret'] = intent.client_secret
        context['payment_intent_id'] = intent.id
    except stripe.error.StripeError:
        pass
    return render(request, 'orders/checkout.html', context)


@require_POST
def create_checkout_session(request):
    """
    Create a Stripe Checkout Session for the current cart and redirect to Stripe.
    User pays on Stripe's hosted page, then is redirected to success/cancel URLs.
    Order is created reliably via webhook (checkout.session.completed) even if user closes tab.
    Uses form POST + redirect (no fetch needed).
    """
    cart = Cart(request)
    if not cart.cart:
        return redirect('cart:cart_detail')
    if not settings.STRIPE_SECRET_KEY:
        return redirect('orders:checkout')
    total = cart.get_total_price()
    amount_cents = int(total * 100)
    if amount_cents < 50:
        return redirect('cart:cart_detail')
    domain = getattr(settings, 'DOMAIN', 'http://localhost:8000')
    base_url = domain.rstrip('/')
    line_items = cart.get_line_items_for_stripe(base_url)
    if not line_items:
        return redirect('cart:cart_detail')
    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=line_items,
            success_url=f'{domain.rstrip("/")}/orders/success/?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{domain.rstrip("/")}/orders/cancel/',
            metadata={'items': _metadata_items_from_cart(cart)},
        )
        return redirect(session.url)
    except stripe.error.StripeError:
        return redirect('orders:checkout')


@require_POST
def update_payment_intent(request):
    """Update PaymentIntent metadata with email before confirm (for order record)."""
    import json
    if not settings.STRIPE_SECRET_KEY:
        return JsonResponse({'error': 'Payment not configured'}, status=500)
    try:
        data = json.loads(request.body)
        pid = (data.get('payment_intent_id') or '').strip()
        email = (data.get('email') or '').strip()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid request'}, status=400)
    if not pid or not pid.startswith('pi_'):
        return JsonResponse({'error': 'Invalid payment intent'}, status=400)
    try:
        intent = stripe.PaymentIntent.retrieve(pid)
        metadata = dict(intent.metadata or {})
        metadata['email'] = email[:254] if email else ''
        stripe.PaymentIntent.modify(pid, metadata=metadata)
        return JsonResponse({'ok': True})
    except stripe.error.StripeError:
        return JsonResponse({'error': 'Could not update payment details'}, status=400)


def checkout_success(request):
    """
    Success template view after payment. Stripe redirects here via return_url.
    Order confirmation is saved to the database (idempotent: same payment never creates duplicate orders).
    """
    payment_intent_id = request.GET.get('payment_intent')
    session_id = request.GET.get('session_id')
    cart = Cart(request)
    user = request.user if request.user.is_authenticated else None

    if payment_intent_id and settings.STRIPE_SECRET_KEY:
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status == 'succeeded':
                email = (intent.metadata or {}).get('email') or ''
                total = Decimal(intent.amount / 100)
                _create_order_from_cart(
                    cart,
                    email=email,
                    stripe_payment_intent_id=payment_intent_id,
                    total=total,
                    user=user,
                )
        except stripe.error.StripeError:
            pass
        order = Order.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
        return render(request, 'orders/success.html', {'order': order})

    if session_id and settings.STRIPE_SECRET_KEY:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                email = session.get('customer_email') or (session.get('customer_details') or {}).get('email', '') or ''
                total = Decimal((session.amount_total or 0) / 100)
                _create_order_from_cart(
                    cart,
                    email=email,
                    stripe_session_id=session_id,
                    total=total,
                    user=user,
                )
        except stripe.error.StripeError:
            pass
        order = Order.objects.filter(stripe_session_id=session_id).first()
        return render(request, 'orders/success.html', {'order': order})

    return redirect('products:home')


def checkout_cancel(request):
    """Shown when user cancels payment on Stripe Checkout page."""
    return render(request, 'orders/cancel.html')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.warning("Stripe webhook received but STRIPE_WEBHOOK_SECRET not configured")
        return HttpResponse(status=200)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.warning("Stripe webhook invalid payload: %s", type(e).__name__)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        return HttpResponse(status=400)

    event_type = event.get('type', '')
    event_id = event.get('id', '')
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        _create_order_from_checkout_session(session)
        logger.info("Stripe webhook processed checkout.session.completed event_id=%s", event_id[:20] if event_id else "")
    elif event_type == 'payment_intent.succeeded':
        intent = event['data']['object']
        _create_order_from_payment_intent_metadata(intent)
        logger.info("Stripe webhook processed payment_intent.succeeded event_id=%s", event_id[:20] if event_id else "")
    return HttpResponse(status=200)
