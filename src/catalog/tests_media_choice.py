from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

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
