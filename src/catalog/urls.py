from django.urls import path

from src.catalog import views

urlpatterns = [
    path("katalog/pidkazky/", views.catalog_suggest, name="catalog_suggest"),
    path("katalog/", views.catalog, name="catalog"),
    path("katalog/<slug:slug>/", views.catalog, name="category"),
    path("tovar/<slug:slug>/", views.product_detail, name="product"),
]
