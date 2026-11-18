"""Фільтр каталогу повторює групи меню в шапці, а не старі категорії."""

from django.urls import reverse

GROUP_KEYS = {
    "Святкові бокси": "svyatkovi-boksy",
    "Столові аксесуари": "stolovi-aksesuary",
}

ACCESSORY_KEYS = {
    "Підсвічники": "pidsvichnyky",
    "Серветки": "servetky",
    "Кільця для серветок": "kiltsia",
}

ACCESSORY_SKUS = {
    "pidsvichnyky": ("ADD-HOLDERS", "ADD-HOLDERS-2", "ADD-HOLDERS-EXTRA"),
    "servetky": ("ADD-NAPKIN", "ADD-NAPKIN-PLAID"),
    "kiltsia": ("ADD-RINGS",),
}


def group_key(group):
    return GROUP_KEYS.get(group.title_uk, "")


def item_key(item):
    if item.collection_id and item.collection.slug:
        return item.collection.slug
    return ACCESSORY_KEYS.get(item.label_uk, "")


def catalog_href(key):
    if not key:
        return reverse("catalog")
    return f"{reverse('catalog')}?menu={key}"


def known_menu_keys():
    from src.content.models import HomeCollection

    keys = set(GROUP_KEYS.values()) | set(ACCESSORY_KEYS.values())
    keys.update(
        HomeCollection.objects.filter(is_active=True)
        .exclude(slug="")
        .values_list("slug", flat=True)
    )
    return keys


def menu_facets():
    from src.content.models_menu import MenuGroup

    facets = []
    groups = (
        MenuGroup.objects.filter(is_active=True)
        .prefetch_related("items__collection")
        .order_by("sort", "id")
    )
    for group in groups:
        key = group_key(group)
        if not key:
            continue
        children = []
        for item in group.items.all():
            if not item.is_active:
                continue
            child_key = item_key(item)
            if not child_key:
                continue
            children.append({"key": child_key, "label": item.label})
        facets.append({"key": key, "label": group.title, "children": children})
    return facets


def product_ids_for_menu(keys):
    from src.content.models import HomeCollection
    from src.content.models_menu import MenuGroupItem

    wanted = []
    keys = [key for key in keys if key]
    if not keys:
        return wanted
    group_by_key = {value: title for title, value in GROUP_KEYS.items()}
    accessory_by_key = {value: label for label, value in ACCESSORY_KEYS.items()}
    for key in keys:
        if key in group_by_key:
            items = MenuGroupItem.objects.filter(
                is_active=True,
                group__title_uk=group_by_key[key],
                group__is_active=True,
            ).select_related("collection__product")
            for item in items:
                if item.collection_id and item.collection.product_id:
                    wanted.append(item.collection.product_id)
                child = item_key(item)
                wanted.extend(_sku_ids(ACCESSORY_SKUS.get(child, ())))
            continue
        collection = (
            HomeCollection.objects.filter(slug=key, is_active=True)
            .only("product_id")
            .first()
        )
        if collection and collection.product_id:
            wanted.append(collection.product_id)
            continue
        label = accessory_by_key.get(key)
        if label:
            wanted.extend(_sku_ids(ACCESSORY_SKUS.get(key, ())))
    return list(dict.fromkeys(wanted))


def _sku_ids(skus):
    from src.catalog.models import Product

    if not skus:
        return []
    return list(
        Product.objects.filter(sku__in=skus, is_active=True).values_list("pk", flat=True)
    )


def accessory_crumb(product):
    from src.content.models_menu import MenuGroupItem

    label_uk = ""
    for label, key in ACCESSORY_KEYS.items():
        if product.sku in ACCESSORY_SKUS.get(key, ()):
            label_uk = label
            break
    if not label_uk:
        return None
    item = (
        MenuGroupItem.objects.filter(
            label_uk=label_uk,
            is_active=True,
            group__is_active=True,
        )
        .select_related("group")
        .order_by("group__sort", "sort", "id")
        .first()
    )
    if item is None:
        return {
            "title": "Столові аксесуари",
            "url": catalog_href("stolovi-aksesuary"),
            "label": label_uk,
        }
    return {
        "title": item.group.title,
        "url": catalog_href(group_key(item.group) or "stolovi-aksesuary"),
        "label": item.label,
    }
