from .cart import Cart

FREE_SHIPPING_THRESHOLD = 75


def cart(request):
    c = Cart(request)
    total = c.get_total_price()
    return {
        'cart': c,
        'free_shipping_threshold': FREE_SHIPPING_THRESHOLD,
        'free_shipping_remaining': max(0, float(FREE_SHIPPING_THRESHOLD) - float(total)),
    }
