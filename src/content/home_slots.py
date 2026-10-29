"""Читання та синхронізація слотів головної з legacy-полями каталогу."""

from src.catalog.models import Category, Product
from src.content.models import HomeBlock
from src.content.models_home_slots import HomeCategorySlot, HomePopularSlot


def categories_block():
    block, _ = HomeBlock.objects.get_or_create(key=HomeBlock.Key.CATEGORIES, defaults={"sort": 2})
    return block


def popular_block():
    block, _ = HomeBlock.objects.get_or_create(key=HomeBlock.Key.POPULAR, defaults={"sort": 4})
    return block


def advantages_block():
    block, _ = HomeBlock.objects.get_or_create(key=HomeBlock.Key.ADVANTAGES, defaults={"sort": 5})
    return block


def home_categories():
    slots = list(
        HomeCategorySlot.objects.filter(block__key=HomeBlock.Key.CATEGORIES, category__is_active=True)
        .select_related("category")
        .order_by("sort", "id")
    )
    if slots:
        return [slot.category for slot in slots]
    return list(
        Category.objects.filter(is_active=True, home_sort__isnull=False).order_by("home_sort", "id")
    )


def home_popular():
    slots = list(
        HomePopularSlot.objects.filter(block__key=HomeBlock.Key.POPULAR, product__is_active=True)
        .select_related("product")
        .prefetch_related("product__images")
        .order_by("sort", "id")
    )
    if slots:
        return [slot.product for slot in slots]
    return list(
        Product.objects.filter(is_active=True, is_popular=True)
        .prefetch_related("images")
        .order_by("sort", "id")
    )


def sync_category_home_sort(block):
    Category.objects.filter(home_sort__isnull=False).update(home_sort=None)
    for slot in HomeCategorySlot.objects.filter(block=block).order_by("sort", "id"):
        Category.objects.filter(pk=slot.category_id).update(home_sort=slot.sort)


def sync_popular_flags(block):
    Product.objects.filter(is_popular=True).update(is_popular=False)
    ids = list(
        HomePopularSlot.objects.filter(block=block).order_by("sort", "id").values_list("product_id", flat=True)
    )
    if ids:
        Product.objects.filter(pk__in=ids).update(is_popular=True)


def about_popular():
    from src.content.models import AboutPage
    from src.content.models_about import AboutPopularSlot

    page = AboutPage.load()
    slots = list(
        AboutPopularSlot.objects.filter(page=page, product__is_active=True)
        .select_related("product")
        .prefetch_related("product__images")
        .order_by("sort", "id")
    )
    if slots:
        return [slot.product for slot in slots]
    return home_popular()
