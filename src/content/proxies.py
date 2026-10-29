from src.content.models import AboutPage, HomeBlock, Review, SiteSettings
from src.content.models_legal import LegalPage


class HomeBannerMedia(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Банер"
        verbose_name_plural = "Банер"


class HomeBannerText(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Текст банера"
        verbose_name_plural = "Текст банера"


class HomeHeroBlock(HomeBlock):
    """Legacy proxy name; admin uses HomeBannerText / HomeBannerMedia."""

    class Meta:
        proxy = True
        verbose_name = "Текст банера"
        verbose_name_plural = "Текст банера"


class HomeCategoriesBlock(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Категорії"
        verbose_name_plural = "Категорії"


class HomeMidBanner(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Банер середній"
        verbose_name_plural = "Банер середній"


class HomeVideoBlock(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Банер середній"
        verbose_name_plural = "Банер середній"


class HomePopularBlock(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Популярні товари"
        verbose_name_plural = "Популярні товари"


class HomeAdvantagesBlock(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Чому обирають"
        verbose_name_plural = "Чому обирають"


class HomeBottomBanner(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Банер нижній"
        verbose_name_plural = "Банер нижній"


class HomeVideo2Block(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Банер нижній"
        verbose_name_plural = "Банер нижній"


class HomeReviewsBlock(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Відгуки"
        verbose_name_plural = "Відгуки"


class HomeCallbackBlock(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Зворотній дзвінок"
        verbose_name_plural = "Зворотній дзвінок"


class AboutIntro(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Інтро"
        verbose_name_plural = "Інтро"


class AboutGallery(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Галерея"
        verbose_name_plural = "Галерея"


class AboutStory(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Історія"
        verbose_name_plural = "Історія"


class AboutBanner(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Банер"
        verbose_name_plural = "Банер"


class AboutReviewsBlock(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Відгуки (Про нас)"
        verbose_name_plural = "Відгуки (Про нас)"


class AboutPopularBlock(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Популярні товари (Про нас)"
        verbose_name_plural = "Популярні товари (Про нас)"


# Сумісність зі старими імпортами адмінки.
AboutPicksBlock = AboutPopularBlock


class HomeReview(Review):
    class Meta:
        proxy = True
        verbose_name = "Відгук (головна)"
        verbose_name_plural = "Список відгуків"


class AboutReview(Review):
    class Meta:
        proxy = True
        verbose_name = "Відгук (Про нас)"
        verbose_name_plural = "Список відгуків (Про нас)"


class OfferPage(LegalPage):
    class Meta:
        proxy = True
        verbose_name = "Публічний договір"
        verbose_name_plural = "Публічний договір"


class PrivacyPolicyPage(LegalPage):
    class Meta:
        proxy = True
        verbose_name = "Політика конфіденційності"
        verbose_name_plural = "Політика конфіденційності"


class CookiePolicyPage(LegalPage):
    class Meta:
        proxy = True
        verbose_name = "Політика cookies"
        verbose_name_plural = "Політика cookies"


class ShippingPage(LegalPage):
    class Meta:
        proxy = True
        verbose_name = "Доставка та оплата"
        verbose_name_plural = "Доставка та оплата"


class FooterChrome(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = "Тексти підвалу"
        verbose_name_plural = "Тексти підвалу"
