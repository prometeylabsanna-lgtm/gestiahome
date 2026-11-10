from django.urls import path

from src.commerce import views

urlpatterns = [
    path("koshik/", views.cart_page, name="cart"),
    path("koshik/panel/", views.cart_panel, name="cart_panel"),
    path("koshik/dodaty/", views.cart_add, name="cart_add"),
    path("koshik/kilkist/", views.cart_update, name="cart_update"),
    path("obrane/", views.wishlist_page, name="wishlist"),
    path("obrane/toggle/", views.wishlist_toggle, name="wishlist_toggle"),
    path("obrane/prybraty/", views.wishlist_remove, name="wishlist_remove"),
    path("zamovlennia/", views.checkout, name="checkout"),
    path("zamovlennia/np/cities/", views.np_cities, name="np_cities"),
    path("zamovlennia/np/warehouses/", views.np_warehouses, name="np_warehouses"),
    path("zamovlennia/np/streets/", views.np_streets, name="np_streets"),
    path("thank-you/", views.thanks, name="thanks"),
    path("diakuiemo/", views.thanks, name="thanks_legacy"),
    path("zayavka/", views.callback, name="callback"),
    path("zamovyty-odrazu/", views.buy_now, name="buy_now"),
    path("zvorotnyi-zvyazok/", views.contact, name="contact"),
    path("svyatkovi-boksy/", views.waitlist, name="waitlist"),
]
