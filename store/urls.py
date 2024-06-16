from django.urls import path
from .import views

urlpatterns = [
    path("", views.index, name="index"),
    path("cart", views.cart, name="cart"),
    path("add_to_cart", views.add_to_cart, name="add"),
    path("dec_cart", views.dec_cart, name="dec"),
    path("del_cart", views.del_cart, name="del"),
    path("confirm_payment/<str:pk>", views.confirm_payment, name="add"),
    path("payment", views.payment, name="payment")
]
