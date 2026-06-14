from django import forms
from accounts.models import User


class CheckoutForm(forms.ModelForm):
    """Checkout form with shipping details."""
    
    class Meta:
        model = User
        fields = ['address', 'city', 'country', 'zip_code', 'phone']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        }
