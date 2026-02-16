from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, Address

User = get_user_model()


class RegisterForm(UserCreationForm):
    """Create account: first name, last name, email, password, confirm password."""
    first_name = forms.CharField(max_length=150, required=True, label='First name')
    last_name = forms.CharField(max_length=150, required=True, label='Last name')
    email = forms.EmailField(required=True, label='Email')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password2'].label = 'Confirm password'
        for name in ('first_name', 'last_name', 'email', 'password1', 'password2'):
            self.fields[name].widget.attrs['class'] = 'form-control'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'
        if 'username' in self.fields:
            del self.fields['username']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        user.email = email
        base = email[:150]
        user.username = base
        while User.objects.filter(username=user.username).exists():
            suffix = str(User.objects.filter(username__startswith=base).count())
            user.username = (base[:150 - len(suffix) - 1] + '_' + suffix)[:150]
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

COUNTRY_CHOICES = [
    ('', 'Select country'),
    ('GB', 'United Kingdom'),
    ('US', 'United States'),
    ('IE', 'Ireland'),
    ('DE', 'Germany'),
    ('FR', 'France'),
    ('ES', 'Spain'),
    ('IT', 'Italy'),
    ('NL', 'Netherlands'),
    ('AU', 'Australia'),
    ('CA', 'Canada'),
    ('IN', 'India'),
]


class ProfileDetailsForm(forms.ModelForm):
    """Form for editing user first name, last name, email."""
    first_name = forms.CharField(max_length=150, required=False, label='First name')
    last_name = forms.CharField(max_length=150, required=False, label='Last name')
    email = forms.EmailField(label='E-mail address')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileExtrasForm(forms.ModelForm):
    """Form for phone and date of birth (Profile model)."""
    phone = forms.CharField(max_length=20, required=False, label='Phone number',
                            help_text='Keep 9-digit format with no spaces and dashes.')
    date_of_birth = forms.DateField(required=False, label='Birth date',
                                    widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'dd/mm/yyyy'}))

    class Meta:
        model = Profile
        fields = ('phone', 'date_of_birth')


class AddressForm(forms.ModelForm):
    """Form for adding/editing a saved address."""
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, required=True)

    class Meta:
        model = Address
        fields = (
            'label', 'first_name', 'last_name',
            'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'phone', 'is_default'
        )
        widgets = {
            'label': forms.TextInput(attrs={'placeholder': 'e.g. Home, Work', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Apartment, suite, etc. (optional)', 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
