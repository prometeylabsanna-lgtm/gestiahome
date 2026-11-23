from django.db import migrations

# English copy for known dev/prod rows. Applied only when the target field is empty.
# Match categories, sets, groups and attributes by slug; products by sku and slug.

CATEGORY_NAMES = {
    "interierni-kompozytsii": "Interior compositions",
    "novorichnyi-dekor": "New Year decor",
    "podarunkovi-sety": "Gift sets",
    "rizdvyani-boksy": "Christmas boxes",
    "serviruvannia": "Table setting",
    "svichky": "Candles",
    "tekstyl": "Textiles",
    "vazy-ta-kashpo": "Vases and planters",
}

SET_NAMES = {
    "velykodni": "Easter",
}

GROUP_NAMES = {
    "color": "Colour",
    "style": "Style",
}

ATTRIBUTE_NAMES = {
    ("color", "beige"): "Beige",
    ("color", "black"): "Black",
    ("color", "gold"): "Gold",
    ("color", "green"): "Green",
    ("color", "red"): "Red",
    ("color", "white"): "White",
    ("style", "boho"): "Boho",
    ("style", "classic"): "Classic",
    ("style", "modern"): "Modern",
    ("style", "rustic"): "Rustic",
    ("style", "scandi"): "Scandinavian",
}

NEST_DESCRIPTION = (
    "The Easter box «The Nest» is a festive arrangement for an atmospheric Easter table.\n"
    "It includes decorative Easter eggs, flower-shaped candle holders, and details for the festive arrangement."
)

PRODUCTS = {
    "GH-01": {
        "slug": "velykodnii-ukrainskyi",
        "name_en": "Easter box «Ukrainian»",
    },
    "GH-02": {
        "slug": "boks-rizdvyanyi-shyshky",
        "name_en": "Christmas box «Pine Cones»",
    },
    "GH-04": {
        "slug": "vesilnyi",
        "name_en": "Wedding box",
    },
    "GH-05": {
        "slug": "vesnianyi",
        "name_en": "Spring box",
    },
    "GH-06": {
        "slug": "gazetnyi",
        "name_en": "Newspaper box",
    },
    "TL-0012": {
        "slug": "velykodnii-hnizdo",
        "name_en": "Easter box «The Nest»",
        "description_en": NEST_DESCRIPTION,
    },
}


def _fill_by_slug(model, mapping, field):
    for slug, value in mapping.items():
        model.objects.filter(slug=slug, **{field: ""}).update(**{field: value})


def _clear_by_slug(model, mapping, field):
    for slug, value in mapping.items():
        model.objects.filter(slug=slug, **{field: value}).update(**{field: ""})


def fill_english_catalog(apps, schema_editor):
    del schema_editor
    Category = apps.get_model("catalog", "Category")
    ProductSet = apps.get_model("catalog", "ProductSet")
    ProductAttributeGroup = apps.get_model("catalog", "ProductAttributeGroup")
    ProductAttribute = apps.get_model("catalog", "ProductAttribute")
    Product = apps.get_model("catalog", "Product")

    _fill_by_slug(Category, CATEGORY_NAMES, "name_en")
    _fill_by_slug(ProductSet, SET_NAMES, "name_en")
    _fill_by_slug(ProductAttributeGroup, GROUP_NAMES, "name_en")
    for (group_slug, slug), name_en in ATTRIBUTE_NAMES.items():
        ProductAttribute.objects.filter(
            group__slug=group_slug,
            slug=slug,
            name_en="",
        ).update(name_en=name_en)
    for sku, copy in PRODUCTS.items():
        row = Product.objects.filter(sku=sku, slug=copy["slug"])
        row.filter(name_en="").update(name_en=copy["name_en"])
        description = copy.get("description_en")
        if description:
            row.filter(description_en="").update(description_en=description)


def clear_english_catalog(apps, schema_editor):
    del schema_editor
    Category = apps.get_model("catalog", "Category")
    ProductSet = apps.get_model("catalog", "ProductSet")
    ProductAttributeGroup = apps.get_model("catalog", "ProductAttributeGroup")
    ProductAttribute = apps.get_model("catalog", "ProductAttribute")
    Product = apps.get_model("catalog", "Product")

    _clear_by_slug(Category, CATEGORY_NAMES, "name_en")
    _clear_by_slug(ProductSet, SET_NAMES, "name_en")
    _clear_by_slug(ProductAttributeGroup, GROUP_NAMES, "name_en")
    for (group_slug, slug), name_en in ATTRIBUTE_NAMES.items():
        ProductAttribute.objects.filter(
            group__slug=group_slug,
            slug=slug,
            name_en=name_en,
        ).update(name_en="")
    for sku, copy in PRODUCTS.items():
        row = Product.objects.filter(sku=sku, slug=copy["slug"])
        row.filter(name_en=copy["name_en"]).update(name_en="")
        description = copy.get("description_en")
        if description:
            row.filter(description_en=description).update(description_en="")


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_remove_russian_fields"),
    ]

    operations = [
        migrations.RunPython(fill_english_catalog, clear_english_catalog),
    ]
