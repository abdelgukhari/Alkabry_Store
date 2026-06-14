from django import forms
from django.contrib.auth import authenticate
from .models import User


class UserRegistrationForm(forms.ModelForm):
    """Form for user registration."""

    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={
        'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amazon-blue focus:border-transparent',
        'placeholder': 'At least 8 characters'
    }))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={
        'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amazon-blue focus:border-transparent',
        'placeholder': 'Re-enter password'
    }))

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amazon-blue focus:border-transparent',
                'placeholder': 'Enter your email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amazon-blue focus:border-transparent',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amazon-blue focus:border-transparent',
                'placeholder': 'Last name'
            }),
        }

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match")
        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get('email')
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """Form for user login."""

    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amazon-blue focus:border-transparent',
        'placeholder': 'Email',
        'type': 'email',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amazon-blue focus:border-transparent',
        'placeholder': 'Password',
    }))
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Invalid email or password.")
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile."""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'date_of_birth',
                  'address', 'city', 'country', 'zip_code')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
