from decimal import Decimal

from django.conf import settings

from .models import Product

CART_SESSION_KEY = "tmaxos_cart"


class Cart:
    """A simple session-backed shopping cart."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if not cart:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart
        self.session.modified = True

    def add(self, product_id, quantity=1, override=False):
        product_id = str(product_id)
        quantity = int(quantity)
        if quantity <= 0:
            return
        if override:
            self.cart[product_id] = quantity
        else:
            self.cart[product_id] = self.cart.get(product_id, 0) + quantity
        self.save()

    def set_quantity(self, product_id, quantity):
        product_id = str(product_id)
        quantity = int(quantity)
        if quantity <= 0:
            self.remove(product_id)
        else:
            self.cart[product_id] = quantity
            self.save()

    def remove(self, product_id):
        self.cart.pop(str(product_id), None)
        self.save()

    def clear(self):
        self.cart = {}
        self.save()

    def save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def count(self):
        return sum(self.cart.values())

    def items(self):
        """Return a list of dicts with product + quantity + line total."""
        items = []
        product_ids = [pid for pid in self.cart.keys() if self.cart.get(pid, 0) > 0]
        products = Product.objects.filter(id__in=product_ids, is_active=True)
        for product in products:
            qty = self.cart.get(str(product.id), 0)
            if qty > 0:
                items.append(
                    {
                        "product": product,
                        "quantity": qty,
                        "line_total": product.price * Decimal(qty),
                    }
                )
        return items

    def totals(self):
        subtotal = sum(item["line_total"] for item in self.items())
        free_shipping_above = getattr(settings, "FREE_SHIPPING_ABOVE", 100000)
        shipping_rate = getattr(settings, "SHIPPING_RATE", 3000)
        shipping = Decimal("0.00")
        if subtotal > 0 and subtotal < Decimal(str(free_shipping_above)):
            shipping = Decimal(str(shipping_rate))
        tax = round(subtotal * Decimal("0.05"), 2)  # 5% VAT
        total = subtotal + shipping + tax
        return {
            "subtotal": round(subtotal, 2),
            "shipping": shipping,
            "tax": tax,
            "total": round(total, 2),
            "free_shipping_above": Decimal(str(free_shipping_above)),
            "qualified_free_shipping": subtotal >= Decimal(str(free_shipping_above)),
            "remaining_for_free_shipping": max(Decimal(str(free_shipping_above)) - subtotal, Decimal("0.00")),
        }

    def is_empty(self):
        return self.count() == 0