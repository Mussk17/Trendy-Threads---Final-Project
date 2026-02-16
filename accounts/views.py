from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm
from django.db import models
from django.views.decorators.http import require_POST
from orders.models import Order

from django.core.mail import send_mail
from django.conf import settings

from .forms import ProfileDetailsForm, ProfileExtrasForm, AddressForm
from .models import Profile, Address


def _send_welcome_email(user):
    """Send welcome email on behalf of Trendy Threads."""
    site_name = getattr(settings, 'SITE_NAME', 'Trendy Threads')
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trendythreads.com')
    subject = f'Welcome to {site_name}'
    message = f'''Hi {user.first_name or user.email},

Thanks for creating an account with {site_name}. We're glad to have you.

You can now sign in to browse our latest styles, save your favourites, and checkout with ease.

If you have any questions, just reply to this email or use Support on our site.

— The {site_name} team
'''
    try:
        send_mail(
            subject,
            message,
            from_email,
            [user.email],
            fail_silently=True,
        )
    except Exception:
        pass


def register(request):
    """Standalone register page – first name, last name, email, password."""
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_welcome_email(user)
            messages.success(request, 'Account created! Please sign in.')
            return redirect('accounts:login')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Standalone login page – username/email and password."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if request.method == 'POST':
        email_or_username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        if '@' in email_or_username:
            try:
                user_obj = User.objects.get(email__iexact=email_or_username)
                email_or_username = user_obj.username
            except User.DoesNotExist:
                pass
        user = authenticate(request, username=email_or_username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'products:home')
            if next_url:
                is_absolute = next_url.startswith(('http://', 'https://', '//'))
                if is_absolute:
                    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                        return redirect(next_url)
                else:
                    return redirect(next_url)
            return redirect('products:home')
        messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html')


def auth_page(request):
    """Redirect /accounts/ to login."""
    return redirect('accounts:login')


@login_required
def profile(request):
    """User profile page with sidebar: My details, Orders, etc."""
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(
        models.Q(user=request.user) | models.Q(email=request.user.email)
    ).order_by('-created_at')

    details_form = ProfileDetailsForm(instance=request.user)
    extras_form = ProfileExtrasForm(instance=profile_obj)
    details_saved = False

    if request.method == 'POST' and request.POST.get('section') == 'details':
        details_form = ProfileDetailsForm(request.POST, instance=request.user)
        extras_form = ProfileExtrasForm(request.POST, instance=profile_obj)
        if details_form.is_valid() and extras_form.is_valid():
            details_form.save()
            extras_form.save()
            messages.success(request, 'Your details have been saved.')
            details_saved = True
            details_form = ProfileDetailsForm(instance=request.user)
            extras_form = ProfileExtrasForm(instance=profile_obj)

    addresses = Address.objects.filter(user=request.user)

    return render(request, 'accounts/profile.html', {
        'orders': orders,
        'details_form': details_form,
        'extras_form': extras_form,
        'profile_obj': profile_obj,
        'addresses': addresses,
    })


@login_required
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            if addr.is_default:
                Address.objects.filter(user=request.user).update(is_default=False)
            addr.save()
            messages.success(request, 'Address added.')
            return redirect('accounts:profile' + '#addressbook')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add address'})


@login_required
def address_edit(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=addr)
        if form.is_valid():
            if form.cleaned_data.get('is_default'):
                Address.objects.filter(user=request.user).exclude(pk=addr.pk).update(is_default=False)
            form.save()
            messages.success(request, 'Address updated.')
            return redirect('accounts:profile' + '#addressbook')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm(instance=addr)
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit address', 'address': addr})


@login_required
@require_POST
def address_delete(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    addr.delete()
    messages.success(request, 'Address removed.')
    return redirect('accounts:profile' + '#addressbook')


@login_required
@require_POST
def address_set_default(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    Address.objects.filter(user=request.user).update(is_default=False)
    addr.is_default = True
    addr.save()
    messages.success(request, 'Default address updated.')
    return redirect('accounts:profile' + '#addressbook')
