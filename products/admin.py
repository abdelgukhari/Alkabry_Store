from django.contrib import admin
from .models import Category, Tag, Product, ProductImage, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active', 'product_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'category', 'price', 'compare_price',
        'stock', 'is_available', 'is_featured', 'avg_rating', 'views_count',
        'purchases_count', 'created_at'
    )
    list_filter = (
        'is_available', 'is_active', 'is_featured', 'category',
        'brand', 'color'
    )
    search_fields = ('name', 'description', 'sku', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_available', 'is_featured')
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'description', 'short_description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('sku', 'stock', 'is_available')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Attributes', {
            'fields': ('brand', 'color', 'size', 'material')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Options', {
            'fields': ('is_featured', 'is_active')
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'is_primary', 'created_at')
    list_filter = ('is_primary',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved')
    search_fields = ('title', 'comment', 'user__email', 'product__name')
