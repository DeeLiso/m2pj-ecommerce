from django import forms
from django.conf import settings

from .models import Order


def _payment_choices():
    choices = [
        ("demo", "Card (Demo payment)"),
        ("kbz", "KBZ Pay (Mobile Wallet)"),
        ("wave", "Wave Money (Mobile Wallet)"),
        ("cod", "Cash on Delivery"),
    ]
    if settings.PAYMENT_METHOD in ("stripe", "demo") and settings.STRIPE_SECRET_KEY:
        choices.append(("stripe", "Credit / Debit card (Stripe)"))
    return choices


class CheckoutForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=_payment_choices,
        initial="demo",
        widget=forms.RadioSelect,
    )
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "form-input"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-input"}))
    phone = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={"class": "form-input"}))
    address_line1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-input"}))
    address_line2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={"class": "form-input"}))
    city = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "form-input"}))
    state = forms.CharField(max_length=120, required=False, widget=forms.TextInput(attrs={"class": "form-input"}))
    postal_code = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"class": "form-input"}))
    country = forms.CharField(max_length=120, required=False, widget=forms.TextInput(attrs={"class": "form-input"}))
    payment_phone = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(
            attrs={"class": "form-input", "placeholder": "e.g. 09 123 456 789"},
        ),
    )
    notes = forms.CharField(
        max_length=500, required=False,
        widget=forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "Order notes (optional)"}),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.cart = kwargs.pop("cart", None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            profile = getattr(self.user, "profile", None)
            if profile:
                initial = self.fields_initial_from_profile(profile)
                for field, value in initial.items():
                    if value and not self.fields[field].initial:
                        self.fields[field].initial = value
            if not self.fields["full_name"].initial:
                name = self.user.get_full_name() or self.user.username
                self.fields["full_name"].initial = name
            if not self.fields["email"].initial:
                self.fields["email"].initial = self.user.email

    def fields_initial_from_profile(self, profile):
        return {
            "email": profile.user.email,
            "phone": profile.phone,
            "address_line1": profile.address_line1,
            "address_line2": profile.address_line2,
            "city": profile.city,
            "state": profile.state,
            "postal_code": profile.postal_code,
            "country": profile.country,
        }

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("payment_method")
        if method in ("kbz", "wave") and not cleaned.get("payment_phone", "").strip():
            self.add_error(
                "payment_phone",
                "Please enter the KBZ Pay / Wave Money number you will send the transfer from.",
            )
        return cleaned

    def build_order(self, totals):
        return Order(
            full_name=self.cleaned_data["full_name"],
            email=self.cleaned_data["email"],
            phone=self.cleaned_data["phone"],
            address_line1=self.cleaned_data["address_line1"],
            address_line2=self.cleaned_data["address_line2"],
            city=self.cleaned_data["city"],
            state=self.cleaned_data["state"],
            postal_code=self.cleaned_data["postal_code"],
            country=self.cleaned_data["country"],
            notes=self.cleaned_data["notes"],
            payment_method=self.cleaned_data["payment_method"],
            payment_phone=self.cleaned_data.get("payment_phone", ""),
            subtotal=totals["subtotal"],
            shipping=totals["shipping"],
            tax=totals["tax"],
            total=totals["total"],
        )