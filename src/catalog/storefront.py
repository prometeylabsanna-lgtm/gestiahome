"""Публічна адреса товару: колекція, якщо картка на неї редіректить."""

from django.db.models import Exists, OuterRef, Prefetch


def public_collections():
    from src.content.models import HomeCollection

    return (
        HomeCollection.objects.filter(is_active=True)
        .exclude(slug="")
        .exclude(slug__isnull=True)
    )


def indexable_categories():
    from src.catalog.models import Category, Product

    own = Product.objects.filter(category=OuterRef("pk"), is_active=True)
    nested = Product.objects.filter(
        category__parent=OuterRef("pk"),
        category__is_active=True,
        is_active=True,
    )
    return (
        Category.objects.filter(is_active=True)
        .filter(Exists(own) | Exists(nested))
        .order_by("sort", "name_uk")
    )


def prefetch_public_collections(lookup="home_collections_as_main"):
    return Prefetch(
        lookup,
        queryset=public_collections().order_by("sort", "id"),
        to_attr="public_collections",
    )


def collection_for_product(product):
    if product is None or not getattr(product, "pk", None):
        return None
    cached = getattr(product, "public_collections", None)
    if cached is not None:
        return cached[0] if cached else None
    return public_collections().filter(product_id=product.pk).order_by("sort", "id").first()


def storefront_url(product) -> str:
    collection = collection_for_product(product)
    if collection is not None:
        return collection.get_absolute_url()
    return product.get_absolute_url()


def indexable_products():
    from src.catalog.models import Product

    redirected = public_collections().filter(product=OuterRef("pk"))
    return Product.objects.filter(is_active=True).exclude(Exists(redirected))
