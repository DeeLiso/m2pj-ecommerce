from django.conf import settings

from .cart import Cart
from .models import Rating, Wishlist


def cart_count(request):
    count = 0
    try:
        count = Cart(request).count()
    except Exception:
        count = 0
    return {"cart_count": count}


def engagement(request):
    wishlist_ids = set()
    user_ratings = {}
    if request.user.is_authenticated:
        wishlist_ids = set(
            Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
        )
        user_ratings = dict(
            Rating.objects.filter(user=request.user).values_list("product_id", "value")
        )
    return {
        "wishlist_ids": wishlist_ids,
        "user_ratings": user_ratings,
        "wishlist_count": len(wishlist_ids),
    }


def support_links(request):
    return {
        "VIBER_LINK": settings.VIBER_LINK,
        "FACEBOOK_MESSENGER_URL": settings.FACEBOOK_MESSENGER_URL,
        "WHATSAPP_LINK": settings.WHATSAPP_LINK,
        "TELEGRAM_URL": settings.TELEGRAM_URL,
    }