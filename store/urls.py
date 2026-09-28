from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.product_list, name="product_list"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    # Engagement (ratings / wishlist)
    path("wishlist/", views.wishlist, name="wishlist"),
    path("product/<int:product_id>/rate/", views.rate_product, name="rate_product"),
    path("product/<int:product_id>/review/", views.product_review, name="product_review"),
    path("product/<int:product_id>/wishlist/", views.toggle_wishlist, name="toggle_wishlist"),
    # Cart
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    # Checkout + payment
    path("checkout/", views.checkout, name="checkout"),
    path("payment/success/<str:reference>/", views.payment_success, name="payment_success"),
    path("payment/cancel/<str:reference>/", views.payment_cancel, name="payment_cancel"),
    # Orders
    path("orders/", views.order_list, name="order_list"),
    path("orders/<str:reference>/", views.order_detail, name="order_detail"),
    # Admin dashboard
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
]