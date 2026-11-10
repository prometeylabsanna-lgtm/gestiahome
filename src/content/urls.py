from django.urls import path

from src.content import views

urlpatterns = [
    path("", views.home, name="home"),
    path("pro-nas/", views.about, name="about"),
    path("kolektsiia/<slug:slug>/", views.collection_detail, name="collection"),
    path("publichnyi-dogovir/", views.offer, name="offer"),
    path("polityka-konfidentsiynosti/", views.privacy, name="privacy"),
    path("polityka-cookies/", views.cookies, name="cookies"),
    path("dostavka-ta-oplata/", views.shipping, name="shipping"),
]
