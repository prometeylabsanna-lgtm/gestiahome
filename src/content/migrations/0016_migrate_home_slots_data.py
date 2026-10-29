from django.db import migrations


def forwards(apps, schema_editor):
    HomeBlock = apps.get_model("content", "HomeBlock")
    Advantage = apps.get_model("content", "Advantage")
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    HomeCategorySlot = apps.get_model("content", "HomeCategorySlot")
    HomePopularSlot = apps.get_model("content", "HomePopularSlot")

    cats = list(Category.objects.filter(home_sort__isnull=False).order_by("home_sort", "id"))
    if cats and not HomeCategorySlot.objects.exists():
        categories_block, _ = HomeBlock.objects.get_or_create(
            key="categories",
            defaults={"sort": 2, "title_uk": "Категорії"},
        )
        for cat in cats:
            HomeCategorySlot.objects.create(
                block_id=categories_block.pk,
                category_id=cat.pk,
                sort=cat.home_sort or 0,
            )

    populars = list(Product.objects.filter(is_popular=True).order_by("sort", "id"))
    if populars and not HomePopularSlot.objects.exists():
        popular_block, _ = HomeBlock.objects.get_or_create(
            key="popular",
            defaults={"sort": 4, "title_uk": "Популярні товари"},
        )
        for index, product in enumerate(populars, start=1):
            HomePopularSlot.objects.create(
                block_id=popular_block.pk,
                product_id=product.pk,
                sort=index,
            )

    advantages_block = HomeBlock.objects.filter(key="advantages").first()
    if advantages_block is None and Advantage.objects.filter(block__isnull=True).exists():
        advantages_block, _ = HomeBlock.objects.get_or_create(
            key="advantages",
            defaults={"sort": 5, "title_uk": "Чому обирають Gestia Home"},
        )
    if advantages_block is not None:
        Advantage.objects.filter(block__isnull=True).update(block_id=advantages_block.pk)


def backwards(apps, schema_editor):
    HomeCategorySlot = apps.get_model("content", "HomeCategorySlot")
    HomePopularSlot = apps.get_model("content", "HomePopularSlot")
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")

    for slot in HomeCategorySlot.objects.all():
        Category.objects.filter(pk=slot.category_id).update(home_sort=slot.sort)
    for slot in HomePopularSlot.objects.all():
        Product.objects.filter(pk=slot.product_id).update(is_popular=True)

    HomeCategorySlot.objects.all().delete()
    HomePopularSlot.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0015_home_slots_and_advantage_block"),
        ("catalog", "0003_product_menu_name_uk"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
