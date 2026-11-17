from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from src.content.models import AboutPage
from src.content.models_faq import FaqPage
from src.content.models_thankyou import ThankYouPage

User = get_user_model()

_SINGLETON_CASES = (
    (
        ThankYouPage,
        (
            "admin:content_thankyouorder_changelist",
            "admin:content_thankyoucontact_changelist",
        ),
        (
            "admin:content_thankyouorder_change",
            "admin:content_thankyoucontact_change",
        ),
    ),
    (
        FaqPage,
        (
            "admin:content_faqheader_changelist",
            "admin:content_faqcontact_changelist",
            "admin:content_faqseo_changelist",
        ),
        (
            "admin:content_faqheader_change",
            "admin:content_faqcontact_change",
            "admin:content_faqseo_change",
        ),
    ),
    (
        AboutPage,
        ("admin:content_aboutintro_changelist",),
        ("admin:content_aboutintro_change",),
    ),
)


class SingletonAdminChangelistPermissionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(
            username="sec06-staff",
            email="sec06-staff@example.com",
            password="pass-word-9",
            is_staff=True,
        )
        self.superuser = User.objects.create_superuser(
            username="sec06-super",
            email="sec06-super@example.com",
            password="pass-word-9",
        )

    def test_staff_without_perms_gets_403_and_does_not_create(self):
        self.client.force_login(self.staff)
        for model, changelists, _changes in _SINGLETON_CASES:
            with self.subTest(model=model.__name__):
                model.objects.all().delete()
                cache.clear()
                before = model.objects.count()
                self.assertEqual(before, 0)
                for name in changelists:
                    response = self.client.get(reverse(name))
                    self.assertEqual(response.status_code, 403, name)
                self.assertEqual(model.objects.count(), before)

    def test_superuser_redirects_to_change(self):
        self.client.force_login(self.superuser)
        for model, changelists, changes in _SINGLETON_CASES:
            with self.subTest(model=model.__name__):
                model.objects.all().delete()
                cache.clear()
                for changelist_name, change_name in zip(changelists, changes):
                    response = self.client.get(reverse(changelist_name))
                    self.assertEqual(response.status_code, 302, changelist_name)
                    obj = model.objects.get()
                    self.assertEqual(
                        response["Location"],
                        reverse(change_name, args=[obj.pk]),
                    )
