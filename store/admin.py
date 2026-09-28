from django.contrib import admin
from django.db.models import Count, DecimalField, F, Sum
from django.utils.html import format_html

from .models import Category, Order, OrderItem, Product, Rating, Wishlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "products_count"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]

    def products_count(self, obj):
        return obj.products.count()

    products_count.short_description = "Products"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "product_name", "price", "quantity", "line_total"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def line_total(self, obj):
        return obj.line_total

    line_total.short_description = "Total"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "category", "brand", "color", "price", "compare_at_price", "stock", "featured", "is_active", "image_tag",
    ]
    list_filter = ["category", "brand", "color", "is_active", "featured"]
    list_editable = ["price", "compare_at_price", "stock", "featured", "is_active"]
    search_fields = ["name", "sku", "brand", "color", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["image_tag", "created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "sku", "category")}),
        ("Pricing", {"fields": ("price", "compare_at_price")}),
        ("Details", {"fields": ("description", "stock", "brand", "color", "image", "image_tag")}),
        ("Visibility", {"fields": ("is_active", "featured")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:48px;width:48px;object-fit:cover;border-radius:8px"/>', obj.image.url)
        return "-"

    image_tag.short_description = "Image"


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "value", "has_comment", "has_photo", "updated_at"]
    list_filter = ["value"]
    search_fields = ["product__name", "user__username", "comment"]
    autocomplete_fields = ["product", "user"]

    def has_comment(self, obj):
        return bool(obj.comment)

    has_comment.short_description = "Comment"
    has_comment.boolean = True

    def has_photo(self, obj):
        return bool(obj.image)

    has_photo.short_description = "Photo"
    has_photo.boolean = True


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "created_at"]
    search_fields = ["user__username", "product__name"]
    autocomplete_fields = ["product", "user"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "reference", "full_name", "email", "total", "status", "payment_method", "created_at",
    ]
    list_filter = ["status", "payment_method", "created_at"]
    list_editable = ["status"]
    search_fields = ["reference", "full_name", "email", "phone"]
    readonly_fields = [
        "reference", "user", "subtotal", "shipping", "tax", "total",
        "payment_id", "payment_phone", "created_at", "updated_at",
    ]
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from django.db.models import Count, Sum
        qs = self.model.objects.all()
        extra_context["totals"] = {
            "orders": qs.count(),
            "revenue": qs.filter(status__in=["paid", "processing", "shipped", "delivered"])
            .aggregate(s=Sum("total"))["s"]
            or 0,
        }
        return super().changelist_view(request, extra_context=extra_context)