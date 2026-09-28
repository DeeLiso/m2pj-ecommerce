from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import CheckoutForm
from .models import Category, Order, OrderItem, Product, Rating, Wishlist


# ---------------------------------------------------------------------------
# Shared product-listing helpers
# ---------------------------------------------------------------------------

def _sorted_products(request, base_qs):
    """Return (qs, context) with search/category/price/sort applied."""
    context = {}

    # search
    query = request.GET.get("q", "").strip()
    if query:
        base_qs = base_qs.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(sku__icontains=query)
        )
    context["search_query"] = query

    # category
    active_category = None
    category_slug = request.GET.get("category", "")
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        base_qs = base_qs.filter(category=active_category)
    context["active_category"] = active_category

    # price
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    for field, value in (("price__gte", min_price), ("price__lte", max_price)):
        if value:
            try:
                base_qs = base_qs.filter(**{field: Decimal(value)})
            except Exception:
                pass
    context["min_price"] = min_price
    context["max_price"] = max_price

    # brand
    brand = request.GET.get("brand", "").strip()
    if brand:
        base_qs = base_qs.filter(brand__iexact=brand)
    context["brand"] = brand

    # color
    color = request.GET.get("color", "").strip()
    if color:
        base_qs = base_qs.filter(color__iexact=color)
    context["color"] = color

    # minimum rating
    min_rating = request.GET.get("min_rating", "").strip()
    if min_rating:
        try:
            base_qs = (
                base_qs.filter(ratings__isnull=False)
                .annotate(avg_rating=Avg("ratings__value"))
                .filter(avg_rating__gte=int(min_rating))
                .distinct()
            )
        except (TypeError, ValueError):
            pass
    context["min_rating"] = min_rating

    # filter option lists (used by the sidebar)
    context["brands"] = list(
        Product.objects.filter(is_active=True)
        .exclude(brand="")
        .values_list("brand", flat=True)
        .distinct()
        .order_by("brand")
    )
    context["colors"] = list(
        Product.objects.filter(is_active=True)
        .exclude(color="")
        .values_list("color", flat=True)
        .distinct()
        .order_by("color")
    )

    # sort
    sort = request.GET.get("sort", "newest")
    sort_options = {
        "newest": ("-created_at", "Sort: Newest"),
        "price_asc": ("price", "Sort: Price ↑"),
        "price_desc": ("-price", "Sort: Price ↓"),
        "name_asc": ("name", "Sort: Name A–Z"),
    }
    order_field = sort_options.get(sort, sort_options["newest"])[0]
    base_qs = base_qs.order_by(order_field)
    context["sort"] = sort
    context["sort_options"] = sort_options

    # categories sidebar
    context["categories"] = (
        Category.objects.annotate(product_count=Count("products")).order_by("name")
    )
    context["total_products"] = base_qs.count()
    return base_qs, context


def _paginate(request, qs, per_page=12):
    paginator = Paginator(qs, per_page)
    page_number = request.GET.get("page", 1)
    return paginator.get_page(page_number)


def _qs_quoted(request):
    params = []
    for key in ("q", "category", "min_price", "max_price", "sort", "brand", "color", "min_rating"):
        if request.GET.get(key):
            params.append(f"{key}={request.GET[key]}")
    return "&".join(params)


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def home(request):
    context = {"categories": Category.objects.annotate(product_count=Count("products"))}
    products = Product.objects.filter(is_active=True)
    context["featured"] = products.filter(featured=True)[:8]
    context["new_arrivals"] = products.order_by("-created_at")[:8]
    context["total_products"] = products.count()
    return render(request, "store/home.html", context)


def product_list(request):
    base_qs = Product.objects.filter(is_active=True).select_related("category")
    qs, context = _sorted_products(request, base_qs)
    context["products"] = _paginate(request, qs)
    context["qs_url"] = _qs_quoted(request)
    context["page_title"] = "Shop All"
    context["page_subtitle"] = "Everything in one place"
    return render(request, "store/product_list.html", context)


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    base_qs = Product.objects.filter(is_active=True, category=category).select_related("category")
    qs, context = _sorted_products(request, base_qs)
    context["products"] = _paginate(request, qs)
    context["qs_url"] = _qs_quoted(request)
    context["page_title"] = category.name
    context["page_subtitle"] = category.description or "Browse this collection"
    return render(request, "store/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category"), slug=slug, is_active=True
    )
    related = (
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(id=product.id)[:4]
    )
    reviews = (
        Rating.objects.filter(product=product)
        .select_related("user")
        .order_by("-created_at")
    )
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, product=product).first()
    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "related": related,
            "reviews": reviews,
            "user_rating_value": user_rating.value if user_rating else 0,
            "user_rating_comment": user_rating.comment if user_rating else "",
        },
    )


# ---------------------------------------------------------------------------
# Engagement (ratings + wishlist + share)
# ---------------------------------------------------------------------------

def wishlist(request):
    if request.user.is_authenticated:
        ids = Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
        products = Product.objects.filter(is_active=True, id__in=ids).select_related("category")
    else:
        products = Product.objects.none()
    return render(request, "store/wishlist.html", {"products": products})


@require_POST
def rate_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "login_required": True}, status=403)
    try:
        value = int(request.POST.get("value", ""))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Invalid rating."}, status=400)
    if value < 1 or value > 5:
        return JsonResponse({"ok": False, "error": "Rating must be between 1 and 5."}, status=400)
    rating, _ = Rating.objects.update_or_create(
        user=request.user, product=product, defaults={"value": value}
    )
    return JsonResponse(
        {
            "ok": True,
            "user_rating": rating.value,
            "average": product.average_rating,
            "count": product.rating_count,
        }
    )


@require_POST
@login_required
def product_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        value = int(request.POST.get("value", ""))
    except (TypeError, ValueError):
        value = 0
    if value < 1 or value > 5:
        messages.error(request, "Please pick a rating between 1 and 5 stars.")
        return redirect(product.get_absolute_url())
    comment = request.POST.get("comment", "").strip()
    rating, created = Rating.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={"value": value, "comment": comment},
    )
    if "image" in request.FILES:
        rating.image = request.FILES["image"]
        rating.save(update_fields=["image", "updated_at"])
    else:
        rating.save(update_fields=["value", "comment", "updated_at"])
    messages.success(request, "Thanks! Your review has been published.")
    return redirect(product.get_absolute_url())


@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "login_required": True}, status=403)
    saved, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        saved.delete()
        return JsonResponse({"ok": True, "saved": False})
    return JsonResponse({"ok": True, "saved": True})


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------

def cart_detail(request):
    cart = Cart(request)
    return render(
        request,
        "store/cart.html",
        {"cart": cart, "cart_items": cart.items(), "totals": cart.totals()},
    )


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError):
        quantity = 1
    cart.add(product.id, quantity=quantity)
    messages.success(request, f'Added "{product.name}" to cart.')
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"count": cart.count()})
    return redirect("store:cart_detail")


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError):
        quantity = 1
    cart.set_quantity(product_id, quantity)
    messages.info(request, "Cart updated.")
    return redirect("store:cart_detail")


def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    messages.info(request, "Item removed from cart.")
    return redirect("store:cart_detail")


# ---------------------------------------------------------------------------
# Checkout + payment
# ---------------------------------------------------------------------------

def checkout(request):
    cart = Cart(request)
    if cart.is_empty():
        messages.info(request, "Your cart is empty.")
        return redirect("store:product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST, user=request.user, cart=cart)
        if form.is_valid():
            order = form.build_order(cart.totals())
            order.user = request.user if request.user.is_authenticated else None
            order.save()

            for item in cart.items():
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    product_name=item["product"].name,
                    price=item["product"].price,
                    quantity=item["quantity"],
                )
            cart.clear()

            method = order.payment_method
            if method == "cod":
                messages.info(request, "Order placed. Pay cash on delivery.")
                return redirect("store:order_detail", reference=order.reference)

            if method in ("kbz", "wave"):
                messages.info(
                    request,
                    "Order placed! Please complete your wallet transfer to confirm your order.",
                )
                return redirect("store:order_detail", reference=order.reference)

            # Default = demo/online payment → mark paid
            order.mark_paid(request.user)
            messages.success(request, "Payment successful.")
            return redirect("store:order_detail", reference=order.reference)
    else:
        form = CheckoutForm(user=request.user, cart=cart)

    return render(
        request,
        "store/checkout.html",
        {
            "form": form,
            "cart": cart,
            "cart_items": cart.items(),
            "totals": cart.totals(),
            "kbz_pay_number": settings.KBZ_PAY_NUMBER,
            "wave_pay_number": settings.WAVE_PAY_NUMBER,
        },
    )


def payment_success(request, reference):
    order = get_object_or_404(Order, reference=reference)
    order.mark_paid(request.user)
    return render(request, "store/payment_success.html", {"order": order})


def payment_cancel(request, reference):
    order = get_object_or_404(Order, reference=reference)
    return render(request, "store/payment_cancel.html", {"order": order})


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "store/order_list.html", {"orders": orders})


def order_detail(request, reference):
    order = get_object_or_404(
        Order.objects.select_related("user").prefetch_related("order_items__product"),
        reference=reference,
    )
    # Guest orders are viewable by reference; signed-in/staff users only see their own.
    if order.user and order.user != request.user and not request.user.is_staff:
        return redirect("store:home")
    return render(
        request,
        "store/order_detail.html",
        {
            "order": order,
            "kbz_pay_number": settings.KBZ_PAY_NUMBER,
            "wave_pay_number": settings.WAVE_PAY_NUMBER,
        },
    )


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect("store:home")

    orders = Order.objects.all()
    paid_statuses = ["paid", "processing", "shipped", "delivered"]
    paid_orders = orders.filter(status__in=paid_statuses)
    context = {
        "total_orders": orders.count(),
        "total_revenue": paid_orders.aggregate(t=Sum("total"))["t"] or Decimal("0"),
        "order_count_today": orders.filter(created_at__date=timezone.localdate()).count(),
        "user_count": User.objects.count(),
        "product_count": Product.objects.count(),
        "status_breakdown": list(orders.values("status").annotate(n=Count("id"))),
        "recent_orders": orders.order_by("-created_at")[:10],
        "low_stock": Product.objects.filter(is_active=True, stock__lte=5).order_by("stock")[:10],
        "recent_customers": User.objects.order_by("-date_joined")[:8],
    }
    return render(request, "store/admin_dashboard.html", context)