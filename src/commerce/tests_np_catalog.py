from decimal import Decimal
import re
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from src.catalog.models import Category, Product
from src.commerce.forms import CheckoutForm
from src.commerce.models import Order
from src.commerce.np_catalog import build_search_text
from src.commerce.np_models import NovaPoshtaCity, NovaPoshtaWarehouse
from src.commerce.novaposhta import NovaPoshtaError


def _warehouse(**kwargs):
    data = {
        "ref": "w1",
        "number": "12",
        "label": "Відділення №12: вул. Хрещатик, 22",
        "city_ref": "kyiv",
        "city_name": "Київ",
        "address": "вул. Хрещатик, 22",
        "kind": "branch",
        "is_active": True,
    }
    data.update(kwargs)
    data["search_text"] = build_search_text(
        data["number"], data["label"], data["address"], data["city_name"]
    )
    return NovaPoshtaWarehouse.objects.create(**data)


def _api_row(index, **extra):
    row = {
        "Ref": f"ref-{index}",
        "Description": f"Відділення №{index}: вул. Тестова, {index}",
        "Number": str(index),
        "CityRef": "city-kyiv",
        "CityDescription": "Київ",
        "SettlementAreaDescription": "Київська",
        "ShortAddress": f"вул. Тестова, {index}",
        "WarehouseStatus": "Working",
        "CategoryOfWarehouse": "Branch",
    }
    row.update(extra)
    return row


def _form_data(**extra):
    data = {
        "name": "Оля",
        "phone": "+380671112233",
        "email": "olya@example.com",
        "delivery_method": Order.Delivery.BRANCH,
        "city": "Київ",
        "branch": "Відділення 1",
        "payment_method": Order.Payment.ON_DELIVERY,
        "consent": "on",
    }
    data.update(extra)
    return data


class WarehouseSearchTests(TestCase):
    def test_one_character_is_empty(self):
        _warehouse()
        response = self.client.get("/zamovlennia/np/warehouses/", {"q": "х"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])

    def test_matches_number_address_case_and_spaces(self):
        _warehouse()
        _warehouse(
            ref="w120",
            number="120",
            label="Відділення №120: вул. Інша, 1",
            address="вул. Інша, 1",
        )
        by_number = self.client.get("/zamovlennia/np/warehouses/", {"q": "12"})
        self.assertEqual(by_number.json()["items"][0]["number"], "12")
        by_address = self.client.get("/zamovlennia/np/warehouses/", {"q": "  ХРЕЩАТИК  "})
        self.assertEqual(by_address.json()["items"][0]["ref"], "w1")

    def test_ukrainian_layout_and_city_filter(self):
        _warehouse()
        _warehouse(
            ref="lviv",
            number="1",
            label="Відділення №1: вул. Хрещатик, 1",
            city_ref="lviv",
            city_name="Львів",
            address="вул. Хрещатик, 1",
        )
        swapped = self.client.get("/zamovlennia/np/warehouses/", {"q": "[h"})
        refs = [item["ref"] for item in swapped.json()["items"]]
        self.assertIn("w1", refs)
        filtered = self.client.get(
            "/zamovlennia/np/warehouses/",
            {"q": "хрещатик", "city_ref": "lviv"},
        )
        self.assertEqual([item["ref"] for item in filtered.json()["items"]], ["lviv"])
        nationwide = self.client.get("/zamovlennia/np/warehouses/", {"q": "хрещатик"})
        self.assertIn("—", nationwide.json()["items"][0]["caption"])

    def test_kind_and_inactive(self):
        _warehouse()
        _warehouse(
            ref="box",
            number="5001",
            label="Поштомат №5001: ТРЦ",
            kind="locker",
            address="ТРЦ",
        )
        _warehouse(ref="closed", number="9", label="Відділення №9: зачинене", is_active=False)
        branch = self.client.get("/zamovlennia/np/warehouses/", {"q": "5001", "kind": "branch"})
        locker = self.client.get("/zamovlennia/np/warehouses/", {"q": "5001", "kind": "locker"})
        closed = self.client.get("/zamovlennia/np/warehouses/", {"q": "зачинене"})
        self.assertEqual(branch.json()["items"], [])
        self.assertEqual(locker.json()["items"][0]["ref"], "box")
        self.assertEqual(closed.json()["items"], [])

    def test_limits_suggestions_to_thirty(self):
        for index in range(40):
            _warehouse(
                ref=f"many-{index}",
                number=str(1000 + index),
                label=f"Відділення №{index}: площа Тест",
                address="площа Тест",
            )
        response = self.client.get("/zamovlennia/np/warehouses/", {"q": "тест"})
        self.assertEqual(len(response.json()["items"]), 30)

    @override_settings(NOVA_POSHTA_API_KEY="", DEBUG=False)
    def test_demo_when_catalog_is_empty(self):
        response = self.client.get(
            "/zamovlennia/np/warehouses/",
            {"q": "хре", "city_ref": "demo-kyiv"},
        )
        self.assertEqual(response.status_code, 200)
        labels = [item["label"] for item in response.json()["items"]]
        self.assertTrue(any("Хрещатик" in label for label in labels))

    def test_cities_come_from_catalog(self):
        NovaPoshtaCity.objects.create(
            ref="kyiv",
            name="Київ, Київська",
            area="Київська",
            search_text="київ, київська",
        )
        with patch("src.commerce.views.novaposhta.search_cities") as search:
            response = self.client.get("/zamovlennia/np/cities/", {"q": "ки"})
        search.assert_not_called()
        self.assertEqual(response.json()["items"][0]["ref"], "kyiv")


class WarehouseSyncTests(TestCase):
    @override_settings(NOVA_POSHTA_API_KEY="")
    def test_command_without_key_does_not_raise(self):
        call_command("sync_nova_poshta")
        self.assertEqual(NovaPoshtaWarehouse.objects.count(), 0)

    @override_settings(NOVA_POSHTA_API_KEY="test-key")
    @patch("src.commerce.np_sync.post_rows")
    def test_sync_reads_every_page_and_deactivates_missing(self, post_rows):
        _warehouse(ref="old", label="Відділення №1: старе", number="1")
        post_rows.side_effect = [
            [_api_row(index) for index in range(500)],
            [_api_row(500), _api_row(501)],
        ]
        call_command("sync_nova_poshta")
        self.assertEqual(NovaPoshtaWarehouse.objects.filter(is_active=True).count(), 502)
        self.assertFalse(NovaPoshtaWarehouse.objects.get(ref="old").is_active)
        self.assertEqual(NovaPoshtaCity.objects.get(ref="city-kyiv").name, "Київ, Київська")
        self.assertEqual(post_rows.call_args_list[0].args[2]["Page"], "1")
        self.assertEqual(post_rows.call_args_list[1].args[2]["Limit"], "500")
        self.assertNotIn("CityRef", post_rows.call_args_list[0].args[2])

    @override_settings(NOVA_POSHTA_API_KEY="test-key")
    @patch("src.commerce.np_sync.post_rows")
    def test_failed_sync_keeps_previous_catalog(self, post_rows):
        _warehouse(ref="old")
        post_rows.side_effect = NovaPoshtaError("Нова пошта недоступна")
        with self.assertRaises(CommandError):
            call_command("sync_nova_poshta")
        self.assertTrue(NovaPoshtaWarehouse.objects.get(ref="old").is_active)


class WarehouseCheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(slug="np-cat", name_uk="Каталог")
        Product.objects.create(
            category=category,
            sku="SNIH",
            slug="snih-np",
            name_uk="Сніг",
            price_uah=Decimal("100"),
            price_eur=Decimal("2"),
            stock_qty=10,
        )
        _warehouse()

    def _signature(self):
        session = self.client.session
        session["cart"] = {"SNIH": 1}
        session["currency"] = "uah"
        session.save()
        html = self.client.get("/zamovlennia/").content.decode()
        match = re.search(r'name="cart_sig" value="([^"]*)"', html)
        self.assertIsNotNone(match)
        return match.group(1), html

    def test_checkout_markup_keeps_branch_field(self):
        _signature, html = self._signature()
        self.assertIn("checkout-suggest.js", html)
        self.assertIn('name="warehouse_ref"', html)
        self.assertIn("data-np-clear", html)
        self.assertIn('role="combobox"', html)

    def test_unknown_ref_is_a_field_error(self):
        signature, _html = self._signature()
        response = self.client.post(
            "/zamovlennia/",
            {
                **_form_data(warehouse_ref="missing", city_ref="kyiv"),
                "cart_sig": signature,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, "Оберіть відділення зі списку")

    def test_selected_ref_is_stored_on_the_order(self):
        signature, _html = self._signature()
        response = self.client.post(
            "/zamovlennia/",
            {
                **_form_data(warehouse_ref="w1", city_ref="kyiv", branch="чернетка"),
                "cart_sig": signature,
            },
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.np_warehouse_ref, "w1")
        self.assertEqual(order.np_city_ref, "kyiv")
        self.assertIn("Хрещатик", order.delivery_address)

    def test_free_text_still_checks_out(self):
        form = CheckoutForm(data=_form_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["warehouse_ref"], "")
