from django.db import migrations


def forwards(apps, schema_editor):
    del schema_editor
    Review = apps.get_model("content", "Review")
    AboutPage = apps.get_model("content", "AboutPage")
    AboutPopularSlot = apps.get_model("content", "AboutPopularSlot")
    HomePopularSlot = apps.get_model("content", "HomePopularSlot")
    HomeBlock = apps.get_model("content", "HomeBlock")
    Product = apps.get_model("catalog", "Product")

    if not Review.objects.filter(placement="about").exists():
        for review in Review.objects.filter(placement="home").order_by("sort", "id"):
            Review.objects.create(
                placement="about",
                author_uk=review.author_uk,
                author_en=review.author_en,
                text_uk=review.text_uk,
                text_en=review.text_en,
                rating_kind=review.rating_kind,
                sort=review.sort,
            )

    page = AboutPage.objects.first()
    if page is None:
        return

    existing = list(
        AboutPopularSlot.objects.filter(page=page).order_by("sort", "id")
    )
    if len(existing) >= 4:
        return

    seen = {slot.product_id for slot in existing}
    next_sort = (existing[-1].sort + 1) if existing else 0

    candidates = []
    popular_block = HomeBlock.objects.filter(key="popular").first()
    if popular_block is not None:
        for slot in (
            HomePopularSlot.objects.filter(block=popular_block, product__is_active=True)
            .order_by("sort", "id")
        ):
            if slot.product_id in seen:
                continue
            candidates.append(slot.product_id)
            seen.add(slot.product_id)

    for product in Product.objects.filter(is_active=True, is_popular=True).order_by(
        "sort", "id"
    ):
        if product.pk in seen:
            continue
        candidates.append(product.pk)
        seen.add(product.pk)

    needed = 4 - len(existing)
    for product_id in candidates[:needed]:
        AboutPopularSlot.objects.get_or_create(
            page=page,
            product_id=product_id,
            defaults={"sort": next_sort},
        )
        next_sort += 1


def backwards(apps, schema_editor):
    del apps, schema_editor


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0026_credit_text_zrobleno"),
        ("catalog", "0018_rename_related_help"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
