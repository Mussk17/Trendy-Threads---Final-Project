from django.shortcuts import redirect, get_object_or_404, render
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import ProductVariant
from .cart import Cart


@require_POST
def cart_add(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))

    if variant.stock_qty <= 0:
        messages.warning(request, 'That item is out of stock and cannot be added.')
        return redirect(next_url)

    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        quantity = 1
    if quantity > variant.stock_qty:
        quantity = variant.stock_qty
        messages.info(request, f'Only {variant.stock_qty} in stock; cart updated to that amount.')
    cart.add(variant.id, quantity=quantity)
    messages.success(request, 'Added to cart.')
    return redirect(next_url)


@require_POST
def cart_update(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    try:
        quantity = max(0, int(request.POST.get('quantity', 0)))
    except (ValueError, TypeError):
        quantity = 0

    if quantity > 0 and variant.stock_qty <= 0:
        messages.warning(request, 'That item is out of stock. Removed from cart.')
        quantity = 0
    elif quantity > variant.stock_qty:
        quantity = variant.stock_qty
        messages.info(request, f'Only {variant.stock_qty} in stock; quantity updated.')
    cart.update(variant.id, quantity)
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, variant_id):
    cart = Cart(request)
    cart.remove(variant_id)
    return redirect('cart:cart_detail')


def cart_detail(request):
    return render(request, 'cart/cart_detail.html')
