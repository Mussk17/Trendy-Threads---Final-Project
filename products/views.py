from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Min, Max
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from .models import Brand, Category, Product, ProductVariant


class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.select_related('brand', 'category').prefetch_related('variants').distinct()
        
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        
        brand_id = self.request.GET.get('brand')
        if brand_id:
            qs = qs.filter(brand_id=brand_id)
        
        q = self.request.GET.get('q', '').strip()
        if q:
            # Fields searched: name, description, materials, care, brand, category, variant color/size/sku
            def search_any_field(term):
                size_choices = dict(ProductVariant.SIZES)
                q_term = (
                    Q(name__icontains=term)
                    | Q(description__icontains=term)
                    | Q(material_summary__icontains=term)
                    | Q(care_summary__icontains=term)
                    | Q(brand__name__icontains=term)
                    | Q(category__name__icontains=term)
                    | Q(category__description__icontains=term)
                    | Q(variants__color__icontains=term)
                    | Q(variants__sku__icontains=term)
                )
                if term.upper() in size_choices:
                    q_term = q_term | Q(variants__size=term.upper())
                return q_term

            # Support both full phrase and keyword search: split into words and match any word in any field
            tokens = [t for t in q.split() if t]
            if not tokens:
                pass
            elif len(tokens) == 1:
                qs = qs.filter(search_any_field(tokens[0])).distinct()
            else:
                # Product matches if it matches at least one keyword in at least one of the searched fields
                combined = search_any_field(tokens[0])
                for token in tokens[1:]:
                    combined = combined | search_any_field(token)
                qs = qs.filter(combined).distinct()
        
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price is not None and min_price != '':
            try:
                qs = qs.filter(variants__price__gte=float(min_price)).distinct()
            except ValueError:
                pass
        if max_price is not None and max_price != '':
            try:
                qs = qs.filter(variants__price__lte=float(max_price)).distinct()
            except ValueError:
                pass
        
        size = self.request.GET.get('size')
        if size:
            qs = qs.filter(variants__size=size, variants__stock_qty__gt=0).distinct()
        else:
            qs = qs.filter(variants__stock_qty__gt=0).distinct()
        
        color = self.request.GET.get('color')
        if color:
            qs = qs.filter(variants__color__iexact=color).distinct()
        
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent=None)
        context['brands'] = Brand.objects.all()
        context['current_category'] = self.kwargs.get('category_slug')
        context['selected_brand'] = self.request.GET.get('brand')
        context['search_query'] = self.request.GET.get('q', '')
        context['filter_size'] = self.request.GET.get('size', '')
        context['filter_color'] = self.request.GET.get('color', '')
        context['filter_min_price'] = self.request.GET.get('min_price', '')
        context['filter_max_price'] = self.request.GET.get('max_price', '')
        price_range = ProductVariant.objects.aggregate(Min('price'), Max('price'))
        context['price_min_global'] = price_range['price__min'] or 0
        context['price_max_global'] = price_range['price__max'] or 500
        all_colors = list(ProductVariant.objects.values_list('color', flat=True).distinct().order_by('color'))
        context['filter_colors'] = sorted(set(all_colors))
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        # Recently viewed: append to session (max 10)
        rv = self.request.session.get('recently_viewed', [])
        if product.id not in rv:
            rv = [product.id] + [x for x in rv if x != product.id][:9]
            self.request.session['recently_viewed'] = rv
            self.request.session.modified = True
        context['variants'] = product.variants.all().order_by('size', 'color')
        context['images'] = product.images.all().order_by('sort_order')
        context['available_sizes'] = product.get_available_sizes()
        context['available_colors'] = product.get_available_colors()
        return context


def home(request):
    featured = Product.objects.filter(variants__stock_qty__gt=0).select_related('brand', 'category').distinct()[:8]
    categories = Category.objects.filter(parent=None)
    rv_ids = request.session.get('recently_viewed', [])[:6]
    recently_viewed = list(Product.objects.filter(id__in=rv_ids, variants__stock_qty__gt=0).select_related('brand', 'category').distinct())
    recently_viewed = sorted(recently_viewed, key=lambda p: rv_ids.index(p.id) if p.id in rv_ids else 999)
    recommended = Product.objects.filter(variants__stock_qty__gt=0).exclude(id__in=[p.id for p in featured[:4]]).select_related('brand', 'category').distinct()[:4]
    return render(request, 'products/home.html', {
        'products': featured,
        'categories': categories,
        'recently_viewed': recently_viewed,
        'recommended': recommended,
    })


def wishlist_view(request):
    wishlist_ids = request.session.get('wishlist', [])
    products = Product.objects.filter(id__in=wishlist_ids, variants__stock_qty__gt=0).select_related('brand', 'category').distinct() if wishlist_ids else []
    return render(request, 'products/wishlist.html', {'products': products})


@require_POST
def wishlist_add(request, product_id):
    wishlist = request.session.get('wishlist', [])
    if product_id not in wishlist:
        wishlist.append(product_id)
        request.session['wishlist'] = wishlist
        request.session.modified = True
    next_url = request.POST.get('next', request.GET.get('next', request.META.get('HTTP_REFERER', '/')))
    return redirect(next_url or 'products:home')


@require_POST
def wishlist_remove(request, product_id):
    wishlist = request.session.get('wishlist', [])
    if product_id in wishlist:
        wishlist.remove(product_id)
        request.session['wishlist'] = wishlist
        request.session.modified = True
    return redirect('products:wishlist')
