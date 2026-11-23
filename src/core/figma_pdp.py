import hashlib
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File

from src.catalog.models import CatalogCell, ProductImage
from src.content.models import HomeBlock

PDP = Path(settings.BASE_DIR) / "docs" / "figma" / "v3" / "d_product_1-8837"
CATALOG = Path(settings.BASE_DIR) / "docs" / "figma" / "catalog"
DESC = (
    "Великодній бокс «Гніздо» — святкова композиція для атмосферного оформлення великоднього столу\n"
    "До боксу входять декоративні великодні яйця, свічники у формі квітів та елементи для створення святкової композиції"
)
SHIP = (
    "Доставка «Новою поштою» по Україні — у відділення, поштомат або кур\u2019єром\n"
    "Термін доставки — орієнтовно 1–3 робочі дні після відправлення\n"
    "Вартість доставки розраховується за тарифами перевізника\n"
    "Після відправлення ви отримаєте номер накладної для відстеження замовлення"
)
PAY = (
    "Онлайн-оплата банківською карткою Visa або Mastercard\n"
    "Оплата за реквізитами банківського рахунку\n"
    "Підтвердження замовлення та деталі оплати надсилаються після оформлення"
)


GALLERY = (
    ("70ca3.png", "103.04"),
    ("e43aa.png", "101.59"),
    ("c5d0f.png", "100.31"),
)


def _save(instance, field, path, name):
    current = getattr(instance, field)
    if getattr(current, "name", ""):
        current.delete(save=False)
    with path.open("rb") as handle:
        current.save(name or path.name, File(handle), save=True)


def seed_pdp(products):
    product = products["GH-03"]
    product.description_uk = DESC
    product.save(update_fields=["description_uk"])
    product.related_manual.add(
        products["GH-01"],
        products["GH-02"],
        products["GH-03"],
        products["GH-04"],
    )
    for sort, filename, height in (
        (1, "70ca3.png", "103.04"),
        (2, "e43aa.png", "101.59"),
        (3, "c5d0f.png", "100.31"),
    ):
        shot = ProductImage(
            product=product,
            sort=sort,
            frame_height=Decimal(height),
            frame_top=Decimal("0"),
        )
        _save(shot, "image", PDP / filename, f"pdp-{filename}")
    for key in ("GH-01", "GH-02", "GH-04"):
        _add_gallery(products[key])
    rows = (
        (1, "GH-02", "", "shysh", "db3d5.png"),
        (2, "GH-06", "Бокс Великодній «Український»", "cover", "729be.png"),
    )
    for sort, sku, label, crop, image in rows:
        cell = CatalogCell.objects.create(
            product=products[sku],
            band=0,
            layout=CatalogCell.Layout.ROW,
            role=CatalogCell.Role.GRID,
            surface=CatalogCell.Surface.PDP_MOBILE,
            slot=CatalogCell.Slot.TILE,
            label_uk=label,
            label_en="Easter box «Ukrainian»" if label == "Бокс Великодній «Український»" else "",
            label_fr="Coffret de Pâques «Ukrainien»" if label == "Бокс Великодній «Український»" else "",
            sort=sort,
            price_uah=Decimal("8990.00"),
            crop=crop,
            name_width=95,
        )
        _save(cell, "image", CATALOG / image, f"pdp-mobile-{sort}-{image}")


def _digest(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def _stored_digest(image):
    if not image.image:
        return ""
    image.image.open("rb")
    try:
        return hashlib.md5(image.image.read()).hexdigest()
    finally:
        image.image.close()


def _add_gallery(product):
    have = {_stored_digest(image) for image in product.images.all()}
    sort = product.images.order_by("-sort").values_list("sort", flat=True).first() or 0
    for filename, height in GALLERY:
        path = PDP / filename
        digest = _digest(path)
        if digest in have:
            continue
        sort += 1
        shot = ProductImage(
            product=product,
            sort=sort,
            frame_height=Decimal(height),
            frame_top=Decimal("0"),
        )
        _save(shot, "image", path, f"{product.slug}-{filename}")
        have.add(digest)


def pdp_blocks():
    return (
        ("pdp_ship", 11, "Доставка", SHIP, "", ""),
        ("pdp_pay", 12, "Оплата", PAY, "", ""),
        ("pdp_set", 13, "Товари з цього ж сету", "", "Товари з цього сету", "Перейти до каталогу"),
        ("pdp_related", 14, "Схожі товари", "", "", "Перейти до каталогу"),
    )


def save_pdp_blocks():
    for key, sort, title, text, mobile, cta in pdp_blocks():
        HomeBlock.objects.create(
            key=key,
            sort=sort,
            title_uk=title,
            text_uk=text,
            text_mobile_uk=mobile,
            cta_uk=cta,
        )
