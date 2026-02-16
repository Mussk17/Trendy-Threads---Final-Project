from .models import Category, Brand


def nav_shop(request):
    """Categories and brands for navbar mega menu."""
    return {
        'nav_categories': Category.objects.filter(parent=None).order_by('name'),
        'nav_brands': Brand.objects.all().order_by('name')[:12],
    }
