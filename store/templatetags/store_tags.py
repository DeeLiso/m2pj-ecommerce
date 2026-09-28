from decimal import Decimal, InvalidOperation

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


def _strip_trailing_zeros(value):
    text = f"{value:.2f}"
    if text.endswith("00"):
        return str(int(value))
    return text.rstrip("0").rstrip(".")


@register.filter
def mmk(value):
    """Format a number as Myanmar Kyat, e.g. 1,250,000 Ks."""
    try:
        value = Decimal(value)
    except (TypeError, ValueError, InvalidOperation):
        return "—"
    return f"{intcomma(_strip_trailing_zeros(value))} Ks"


@register.filter
def status_color(status):
    colors = {
        "pending": "bg-amber-100 text-amber-800",
        "paid": "bg-blue-100 text-blue-800",
        "processing": "bg-indigo-100 text-indigo-800",
        "shipped": "bg-purple-100 text-purple-800",
        "delivered": "bg-emerald-100 text-emerald-800",
        "cancelled": "bg-red-100 text-red-800",
    }
    return colors.get(status, "bg-slate-100 text-slate-700")


@register.filter
def get_item(dictionary, key):
    """Look up a key in a dict, e.g. {{ user_ratings|get_item:product.id }}."""
    try:
        return dictionary.get(key, 0)
    except (AttributeError, TypeError):
        return 0