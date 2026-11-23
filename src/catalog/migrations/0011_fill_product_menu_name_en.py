from django.db import migrations

# English menu labels for rows whose Ukrainian menu name is not the product name.
# Matched by sku. Same-name rows copy name_en. Empty targets are left untouched.
MENU_NAME_EN_BY_SKU = {
    "GH-02": "Christmas box «Pine Cones»",
}


def _menu_name_en(product):
    if not product.menu_name_uk:
        return ""
    if product.menu_name_uk == product.name_uk:
        return product.name_en
    return MENU_NAME_EN_BY_SKU.get(product.sku, "")


def fill_menu_name_en(apps, schema_editor):
    del schema_editor
    Product = apps.get_model("catalog", "Product")
    for product in Product.objects.filter(menu_name_en="").iterator():
        value = _menu_name_en(product)
        if value:
            Product.objects.filter(pk=product.pk, menu_name_en="").update(menu_name_en=value)


def clear_menu_name_en(apps, schema_editor):
    del schema_editor
    Product = apps.get_model("catalog", "Product")
    for product in Product.objects.iterator():
        expected = _menu_name_en(product)
        if expected and product.menu_name_en == expected:
            Product.objects.filter(pk=product.pk, menu_name_en=expected).update(menu_name_en="")


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0010_product_menu_name_en"),
    ]

    operations = [
        migrations.RunPython(fill_menu_name_en, clear_menu_name_en),
    ]
