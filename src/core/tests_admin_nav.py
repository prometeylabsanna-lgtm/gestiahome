from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import translation

from src.core.admin_nav import NAV_TREE, build_navigation, iter_nav_entries


class SidebarTreeTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.user = User.objects.create_superuser("editor", "editor@example.com", "pass-word-9")
        self.client.force_login(self.user)

    def test_home_items_follow_page_order(self):
        home = next(g["items"] for g in NAV_TREE if g["title"] == "Головна")
        keys = [entry["key"] for entry in home]
        self.assertEqual(
            keys,
            [
                "home_banner",
                "home_banner_text",
                "home_categories",
                "home_mid_banner",
                "home_popular",
                "home_advantages",
                "home_bottom_banner",
                "home_reviews",
                "home_callback",
            ],
        )
        reviews = next(entry for entry in home if entry["key"] == "home_reviews")
        self.assertEqual(
            [child["key"] for child in reviews.get("items") or []],
            ["home_review_list"],
        )
        self.assertNotIn("home_advantage_cards", keys)
        self.assertNotIn("home_cta", keys)

    def test_pending_entries_stay_in_the_tree(self):
        keys = {entry["key"] for entry in iter_nav_entries(NAV_TREE)}
        self.assertIn("discount", keys)
        self.assertIn("styles", keys)
        self.assertIn("recent_actions", keys)
        self.assertIn("legal_offer", keys)
        self.assertIn("about_intro", keys)
        self.assertIn("about_gallery", keys)
        self.assertIn("about_story", keys)
        self.assertIn("about_banner", keys)
        self.assertIn("about_popular", keys)
        self.assertIn("about_reviews", keys)
        self.assertIn("about_review_list", keys)
        self.assertNotIn("home_cta", keys)
        self.assertNotIn("chrome_footer_links", keys)
        self.assertNotIn("home_video", keys)
        self.assertNotIn("home_video_2", keys)

    def test_navigation_skips_missing_urls(self):
        groups = build_navigation(None)
        titles = [group["title"] for group in groups]
        self.assertIn("Головна", titles)
        self.assertIn("Каталог", titles)
        self.assertIn("Юридичні сторінки", titles)
        self.assertIn("Знижка", titles)
        self.assertIn("Стилі", titles)
        self.assertIn("Система", titles)
        labels = _labels(groups)
        self.assertIn("Недавні дії", labels)
        self.assertIn("Банер", labels)
        self.assertIn("Текст банера", labels)
        self.assertIn("Банер середній", labels)
        self.assertIn("Банер нижній", labels)
        self.assertIn("Чому обирають", labels)
        self.assertIn("Список переваг", labels)
        self.assertIn("Зворотній дзвінок", labels)
        self.assertIn("Відгуки", labels)
        self.assertIn("Список відгуків", labels)
        self.assertIn("Інтро", labels)
        self.assertIn("Галерея", labels)
        self.assertIn("Історія", labels)
        self.assertIn("Популярні товари", labels)
        self.assertNotIn("CTA та контактні форми", labels)
        self.assertNotIn("Посилання футера", labels)
        self.assertNotIn("Головний банер", labels)
        self.assertNotIn("Картки переваг", labels)
        self.assertNotIn("Увесь сайт", labels)
        self.assertEqual(labels.count("Стилі"), 1)

    def test_admin_index_renders_ukrainian_tree(self):
        self.client.cookies["django_language"] = "en"
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestia Home")
        self.assertContains(response, "Головна")
        self.assertContains(response, "Текст банера")
        self.assertContains(response, reverse("admin:content_homebannertext_changelist"))
        self.assertContains(response, reverse("admin:content_homemidbanner_changelist"))
        self.assertContains(response, reverse("admin:content_globalpagestyle_changelist"))
        self.assertContains(response, reverse("admin:admin_logentry_changelist"))
        self.assertContains(response, "Недавні дії")
        self.assertNotContains(response, "id=\"content-related\"")
        self.assertContains(response, "Про нас")
        with self.assertRaises(NoReverseMatch):
            reverse("admin:content_contactforms_changelist")
        with self.assertRaises(NoReverseMatch):
            reverse("admin:content_footerlink_changelist")
        self.assertContains(response, "Інтро")
        self.assertContains(response, reverse("admin:content_aboutintro_changelist"))
        self.assertContains(response, "Замовлення і заявки")
        self.assertContains(response, "Хедер і футер")
        self.assertContains(response, "Користувачі")
        self.assertContains(response, "Вийти")
        self.assertContains(response, "Знижка")
        self.assertNotContains(response, "homevideoblock")
        self.assertNotContains(response, "homeheroblock")
        with self.assertRaises(NoReverseMatch):
            reverse("admin:content_homeheroblock_changelist")

    def test_unfold_changelist_actions_are_ukrainian(self):
        page = self.client.get(reverse("admin:catalog_product_changelist"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Скинути фільтри")
        self.assertContains(page, "Виконати")
        self.assertContains(page, "Виберіть дію")
        self.assertNotContains(page, "Reset filters")
        self.assertNotContains(page, "Select action")
        self.assertNotRegex(page.content.decode(), r">\s*Run\s*<")

    def test_user_and_group_changelists_open(self):
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:auth_group_changelist")).status_code, 200)


class UserDeleteGuardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("owner", "owner@example.com", "pass-word-9")
        self.admin = admin.site._registry[User]
        self.request = RequestFactory().post("/users/")
        self.request.user = self.user
        self.request.session = SessionStore()
        self.request._messages = FallbackStorage(self.request)

    def test_cannot_delete_self_or_last_superuser(self):
        self.assertFalse(self.admin.has_delete_permission(self.request, self.user))
        with self.assertRaises(PermissionDenied):
            self.admin.delete_model(self.request, self.user)
        self.admin.delete_queryset(self.request, User.objects.filter(pk=self.user.pk))
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_batch_keeps_a_superuser(self):
        other = User.objects.create_superuser("other", "other@example.com", "pass-word-9")
        self.admin.delete_queryset(self.request, User.objects.filter(pk__in=[self.user.pk, other.pk]))
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(User.objects.filter(pk=other.pk).exists())


def _labels(groups):
    found = []
    for group in groups:
        for item in group["items"]:
            found.append(item["title"])
            for child in item.get("items") or []:
                found.append(child["title"])
    return found
