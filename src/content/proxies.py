from src.content.models import AboutPage, HomeBlock, Review, SiteSettings
from src.content.models_faq import FaqPage
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


class HomeCollectionsBlock(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Колекції"
        verbose_name_plural = "Колекції"


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


class HomeLocaleBlock(HomeBlock):
    class Meta:
        proxy = True
        verbose_name = "Країна та мова"
        verbose_name_plural = "Країна та мова"


class AboutIntro(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Інтро"
        verbose_name_plural = "Інтро"


class AboutGestia(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Гестія"
        verbose_name_plural = "Гестія"


class AboutApproach(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Підхід"
        verbose_name_plural = "Підхід"


class AboutTogether(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Разом"
        verbose_name_plural = "Разом"


class AboutClosing(AboutPage):
    class Meta:
        proxy = True
        verbose_name = "Фінал і кнопка"
        verbose_name_plural = "Фінал і кнопка"


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


class FaqHeader(FaqPage):
    class Meta:
        proxy = True
        verbose_name = "Шапка і фото"
        verbose_name_plural = "Шапка і фото"


class FaqContact(FaqPage):
    class Meta:
        proxy = True
        verbose_name = "Залишились питання?"
        verbose_name_plural = "Залишились питання?"


class FaqSeo(FaqPage):
    class Meta:
        proxy = True
        verbose_name = "SEO"
        verbose_name_plural = "SEO"


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
