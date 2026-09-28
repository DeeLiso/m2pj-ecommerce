import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    sku = models.CharField(max_length=60, blank=True)
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE
    )
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=100, blank=True, help_text="e.g. T-MAX-OS, Samsung, Sony.")
    color = models.CharField(max_length=100, blank=True, help_text="e.g. Black, White, Silver, Gold.")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Original price shown struck through when on sale.",
    )
    stock = models.PositiveIntegerField(default=0, help_text="Units available in stock.")
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{uuid.uuid4().hex[:6]}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    @property
    def on_sale(self):
        return bool(
            self.compare_at_price and self.compare_at_price > self.price
        )

    @property
    def discount_percent(self):
        if not self.on_sale:
            return 0
        return round(
            (self.compare_at_price - self.price)
            / self.compare_at_price * 100
        )

    def in_stock(self):
        return self.stock > 0

    @property
    def average_rating(self):
        avg = self.ratings.aggregate(models.Avg("value"))["value__avg"]
        return round(avg, 1) if avg is not None else None

    @property
    def rating_count(self):
        return self.ratings.count()

    @property
    def saved_count(self):
        return self.wishlist_items.count()


class Rating(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="ratings", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, related_name="ratings", on_delete=models.CASCADE
    )
    value = models.PositiveSmallIntegerField(
        choices=[(i, f"{i} star{'s' if i > 1 else ''}") for i in range(1, 6)],
        default=5,
    )
    comment = models.TextField(blank=True, help_text="Written review / experience.")
    image = models.ImageField(upload_to="reviews/", blank=True, null=True, help_text="Photo of the product.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} → {self.product}: {self.value}★"


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="wishlisted", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, related_name="wishlist_items", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ♥ {self.product}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    PAYMENT_CHOICES = [
        ("demo", "Card (Demo payment)"),
        ("kbz", "KBZ Pay"),
        ("wave", "Wave Money"),
        ("cod", "Cash on Delivery"),
    ]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=120, default="Myanmar")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="demo")
    payment_id = models.CharField(max_length=200, blank=True)
    payment_phone = models.CharField(
        max_length=30, blank=True,
        help_text="Customer's KBZ Pay / Wave Money number used for the transfer.",
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_reference():
        return f"TMAX-{uuid.uuid4().hex[:10].upper()}"

    def __str__(self):
        return f"Order {self.reference}"

    def mark_paid(self, user=None):
        self.status = "paid"
        self.save(update_fields=["status", "updated_at"])

    @property
    def items(self):
        return self.order_items.all()

    ORDER_FLOW = ["pending", "paid", "processing", "shipped", "delivered"]

    @property
    def status_level(self):
        if self.status == "cancelled":
            return len(self.ORDER_FLOW)
        return self.ORDER_FLOW.index(self.status) + 1

    @property
    def status_steps(self):
        labels = {
            "pending": "Pending",
            "paid": "Paid",
            "processing": "Processing",
            "shipped": "Shipped",
            "delivered": "Delivered",
        }
        return [
            (i + 1, labels.get(step, step.replace("_", " ").title()))
            for i, step in enumerate(self.ORDER_FLOW)
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="order_items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="order_items", on_delete=models.SET_NULL, null=True, blank=True
    )
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to="orders/", blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def line_total(self):
        from decimal import Decimal
        return round(self.price * Decimal(self.quantity), 2)