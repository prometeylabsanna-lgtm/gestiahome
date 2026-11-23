from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from src.catalog.models import Category, Product, ProductImage
from src.content.media import MediaChoice


def _video(name="clip.mp4"):
    return SimpleUploadedFile(name, b"fake-mp4", content_type="video/mp4")


class CatalogMediaChoiceTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(slug="cat", name_uk="Каталог")
        self.product = Product.objects.create(
            category=self.category,
            sku="SKU-1",
            slug="box",
            name_uk="Бокс",
            price_uah=Decimal("10"),
            price_eur=Decimal("1"),
            stock_qty=1,
        )

    def test_category_shows_video(self):
        self.category.media_kind = MediaChoice.Kind.VIDEO
        self.category.video = _video()
        self.category.save()
        self.assertTrue(self.category.shows_video)
        self.assertIsNone(self.category.still_image)

    def test_product_card_media_prefers_own_video(self):
        shot = ProductImage.objects.create(product=self.product, sort=0)
        shot.media_kind = MediaChoice.Kind.VIDEO
        shot.video = _video("gallery.mp4")
        shot.save()
        self.product.media_kind = MediaChoice.Kind.VIDEO
        self.product.video = _video("card.mp4")
        self.product.save()
        self.assertTrue(self.product.shows_card_video)
        self.assertIs(self.product.card_media, self.product)

    def test_product_card_falls_back_to_cover_video(self):
        shot = ProductImage(product=self.product, sort=0)
        shot.media_kind = MediaChoice.Kind.VIDEO
        shot.video = _video("cover.mp4")
        shot.save()
        self.assertTrue(self.product.shows_card_video)
        self.assertEqual(self.product.card_media.pk, shot.pk)

    def test_gallery_item_blank_image_ok_with_video(self):
        shot = ProductImage(product=self.product, sort=1)
        shot.media_kind = MediaChoice.Kind.VIDEO
        shot.video = _video("shot.mp4")
        shot.save()
        self.assertTrue(shot.shows_video)
        self.assertFalse(bool(shot.image))

    def test_pdp_gallery_renders_extra_photo_and_video(self):
        raw = BytesIO()
        Image.new("RGB", (4, 4), (10, 20, 30)).save(raw, format="PNG")
        ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile("shot.png", raw.getvalue(), content_type="image/png"),
            sort=0,
        )
        clip = ProductImage(product=self.product, sort=1)
        clip.media_kind = MediaChoice.Kind.VIDEO
        clip.video = _video("pdp.mp4")
        clip.save()
        page = self.client.get("/tovar/box/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "nd-pdp-gallery__item", count=2)
        self.assertContains(page, "<video")
        self.assertContains(page, "/media/products/video/")
        self.assertContains(page, "/media/products/shot")
