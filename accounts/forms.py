from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-input", "placeholder": "you@example.com", "autocomplete": "email"}
        ),
    )
    full_name = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Your full name"}),
    )
    phone = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "+95 9 xxx xxx xxx"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "full_name", "phone", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-input", "placeholder": "Choose a username", "autocomplete": "username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-input pr-12", "placeholder": "At least 8 characters", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-input pr-12", "placeholder": "Repeat your password", "autocomplete": "new-password"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        full_name = self.cleaned_data.get("full_name", "").strip()
        if full_name:
            parts = full_name.split(" ", 1)
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = parts[1]
        phone = self.cleaned_data.get("phone", "")
        Profile.objects.update_or_create(
            user=user, defaults={"phone": phone, "country": "Myanmar"}
        )
        if commit:
            from django.db import transaction

            with transaction.atomic():
                user.save(update_fields=["first_name", "last_name", "email"])
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-input", "placeholder": "Username", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-input pr-12", "placeholder": "Password", "autocomplete": "current-password"}
        )


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=False, max_length=150,
                                 widget=forms.TextInput(attrs={"class": "form-input"}))
    last_name = forms.CharField(required=False, max_length=150,
                                widget=forms.TextInput(attrs={"class": "form-input"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-input"}))

    class Meta:
        model = Profile
        fields = ["address_line1", "address_line2", "city", "state", "postal_code", "country"]
        widgets = {
            "address_line1": forms.TextInput(attrs={"class": "form-input", "placeholder": "Street address"}),
            "address_line2": forms.TextInput(attrs={"class": "form-input", "placeholder": "Apartment, suite..."}),
            "city": forms.TextInput(attrs={"class": "form-input", "placeholder": "City"}),
            "state": forms.TextInput(attrs={"class": "form-input", "placeholder": "State / Region"}),
            "postal_code": forms.TextInput(attrs={"class": "form-input", "placeholder": "Postal code"}),
            "country": forms.TextInput(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, "user"):
            self.fields["email"].initial = self.instance.user.email
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
        user = profile.user
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.email = self.cleaned_data.get("email")
        if commit:
            user.save(update_fields=["first_name", "last_name", "email"])
        return profile