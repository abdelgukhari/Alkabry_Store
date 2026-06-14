from django import forms
from .models import Review, Product, ProductImage, Category

tw = 'w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amazon-blue'


class ReviewForm(forms.ModelForm):
    """Form for submitting product reviews."""

    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Review title'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review here...'
            }),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description',
            'price', 'compare_price', 'cost_price',
            'sku', 'stock', 'is_available',
            'category', 'brand', 'color', 'size', 'material',
            'image',
            'is_featured', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': tw}),
            'description': forms.Textarea(attrs={'class': tw, 'rows': 5}),
            'short_description': forms.TextInput(attrs={'class': tw}),
            'price': forms.NumberInput(attrs={'class': tw, 'step': '0.01', 'min': '0'}),
            'compare_price': forms.NumberInput(attrs={'class': tw, 'step': '0.01', 'min': '0'}),
            'cost_price': forms.NumberInput(attrs={'class': tw, 'step': '0.01', 'min': '0'}),
            'sku': forms.TextInput(attrs={'class': tw}),
            'stock': forms.NumberInput(attrs={'class': tw, 'min': '0'}),
            'brand': forms.TextInput(attrs={'class': tw}),
            'color': forms.TextInput(attrs={'class': tw}),
            'size': forms.TextInput(attrs={'class': tw}),
            'material': forms.TextInput(attrs={'class': tw}),
            'category': forms.Select(attrs={'class': tw}),
            'image': forms.ClearableFileInput(attrs={'class': tw}),
            'is_available': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amazon-blue rounded'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amazon-blue rounded'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amazon-blue rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['compare_price'].required = False
        self.fields['cost_price'].required = False
        self.fields['image'].required = False


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': tw}),
            'alt_text': forms.TextInput(attrs={'class': tw, 'placeholder': 'Image description'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-amazon-blue rounded'}),
        }
