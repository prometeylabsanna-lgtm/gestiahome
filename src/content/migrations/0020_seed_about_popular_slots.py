from django.db import migrations


def forwards(apps, schema_editor):
    AboutPage = apps.get_model("content", "AboutPage")
    AboutPick = apps.get_model("content", "AboutPick")
    AboutPopularSlot = apps.get_model("content", "AboutPopularSlot")
    Product = apps.get_model("catalog", "Product")
    page = AboutPage.objects.first()
    if page is None:
        return
    if AboutPopularSlot.objects.filter(page=page).exists():
        return
    sort = 0
    for pick in AboutPick.objects.filter(page=page).order_by("sort", "id"):
        slug = (pick.slug or "").strip()
        if not slug:
            continue
        product = Product.objects.filter(slug=slug).first()
        if product is None:
            continue
        AboutPopularSlot.objects.get_or_create(
            page=page,
            product=product,
            defaults={"sort": sort},
        )
        sort += 1
    if not page.reviews_title_uk:
        page.reviews_title_uk = "Відгуки"
    if not page.popular_title_uk:
        page.popular_title_uk = "Популярні товари"
    if not page.popular_cta_uk:
        page.popular_cta_uk = "Перейти до каталогу"
    page.save(
        update_fields=[
            "reviews_title_uk",
            "popular_title_uk",
            "popular_cta_uk",
        ]
    )


def backwards(apps, schema_editor):
    AboutPopularSlot = apps.get_model("content", "AboutPopularSlot")
    AboutPopularSlot.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0019_about_reviews_popular_filters"),
        ("catalog", "0017_about_reviews_popular_filters"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
