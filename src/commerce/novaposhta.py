from __future__ import annotations

import logging
import re
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

API_URL = "https://api.novaposhta.ua/v2.0/json/"
PAGE_SIZE = 500
REQUEST_TIMEOUT = 12

# Trailing house number: 13, 13а, 13/2, 13-А (optional comma after street).
_HOUSE_RE = re.compile(
    r"^(?P<street>.+?)(?:,|\s)+(?P<house>\d+[А-Яа-яA-Za-z]?(?:[/\-]\d+[А-Яа-яA-Za-z]?)?)\s*$",
    re.UNICODE,
)


def split_street_query(query: str) -> tuple[str, str]:
    """Return (street_name, house_number). House may be empty."""
    q = (query or "").strip()
    match = _HOUSE_RE.match(q)
    if not match:
        return q, ""
    return match.group("street").strip(), match.group("house").strip()

# Local/demo data when API key is absent and DEBUG=True.
DEMO_CITIES = [
    {"ref": "demo-kyiv", "name": "м. Київ, Київська обл."},
    {"ref": "demo-kyiv-svyat", "name": "м. Київ, Святошинський р-н"},
    {"ref": "demo-bila", "name": "м. Біла Церква, Київська обл."},
    {"ref": "demo-lviv", "name": "м. Львів, Львівська обл."},
    {"ref": "demo-odesa", "name": "м. Одеса, Одеська обл."},
    {"ref": "demo-kharkiv", "name": "м. Харків, Харківська обл."},
    {"ref": "demo-dnipro", "name": "м. Дніпро, Дніпропетровська обл."},
]

DEMO_WAREHOUSES = {
    "demo-kyiv": [
        {"ref": "demo-w1", "label": "Відділення №1: вул. Хрещатик, 22", "number": "1"},
        {"ref": "demo-w2", "label": "Відділення №2: вул. Велика Васильківська, 100", "number": "2"},
        {"ref": "demo-w3", "label": "Відділення №5: просп. Перемоги, 14", "number": "5"},
        {"ref": "demo-w4", "label": "Відділення №12: вул. Саксаганського, 33", "number": "12"},
    ],
    "demo-kyiv-svyat": [
        {"ref": "demo-w5", "label": "Відділення №88: вул. Якуба Коласа, 10", "number": "88"},
    ],
    "demo-bila": [
        {"ref": "demo-w6", "label": "Відділення №1: вул. Ярослава Мудрого, 15", "number": "1"},
    ],
    "demo-lviv": [
        {"ref": "demo-w7", "label": "Відділення №1: пл. Ринок, 1", "number": "1"},
        {"ref": "demo-w8", "label": "Відділення №3: вул. Городоцька, 175", "number": "3"},
    ],
    "demo-odesa": [
        {"ref": "demo-w9", "label": "Відділення №1: вул. Дерибасівська, 12", "number": "1"},
    ],
    "demo-kharkiv": [
        {"ref": "demo-w10", "label": "Відділення №1: вул. Сумська, 25", "number": "1"},
    ],
    "demo-dnipro": [
        {"ref": "demo-w11", "label": "Відділення №1: просп. Дмитра Яворницького, 50", "number": "1"},
    ],
}

DEMO_LOCKERS = {
    "demo-kyiv": [
        {"ref": "demo-l1", "label": "Поштомат №5001: ТРЦ Gulliver, Спортивна пл., 1а", "number": "5001"},
        {"ref": "demo-l2", "label": "Поштомат №5002: вул. Хрещатик, 15", "number": "5002"},
    ],
}

DEMO_STREETS = {
    "demo-kyiv": [
        {"ref": "demo-s1", "label": "вул. Хрещатик"},
        {"ref": "demo-s2", "label": "вул. Каштанова"},
        {"ref": "demo-s3", "label": "вул. Велика Васильківська"},
        {"ref": "demo-s4", "label": "вул. Саксаганського"},
        {"ref": "demo-s5", "label": "просп. Перемоги"},
        {"ref": "demo-s6", "label": "вул. Богдана Хмельницького"},
    ],
    "demo-lviv": [
        {"ref": "demo-s7", "label": "вул. Городоцька"},
        {"ref": "demo-s8", "label": "пл. Ринок"},
    ],
}


def _api_key() -> str:
    return (getattr(settings, "NOVA_POSHTA_API_KEY", "") or "").strip()


def configured() -> bool:
    return bool(_api_key())


def demo_mode() -> bool:
    """Підказки без API-ключа (локальний список), щоб checkout працював без НП."""
    return not configured()


def _demo_cities(query: str, *, limit: int = 8) -> list[dict[str, str]]:
    needle = query.casefold()
    matched = [c for c in DEMO_CITIES if needle in c["name"].casefold()]
    return matched[:limit]


def _demo_warehouses(city_ref: str, *, kind: str = "branch") -> list[dict[str, str]]:
    if kind == "locker":
        return list(DEMO_LOCKERS.get(city_ref, []))
    return list(DEMO_WAREHOUSES.get(city_ref, DEMO_WAREHOUSES.get("demo-kyiv", [])))


def _demo_streets(city_ref: str, query: str, *, limit: int = 20) -> list[dict[str, str]]:
    street_q, _house = split_street_query(query)
    needle = street_q.casefold()
    rows = DEMO_STREETS.get(city_ref, DEMO_STREETS.get("demo-kyiv", []))
    if needle:
        rows = [row for row in rows if needle in row["label"].casefold()]
    return rows[:limit]


def _post(model: str, method: str, props: dict[str, Any]) -> list[dict[str, Any]]:
    key = _api_key()
    if not key:
        return []
    try:
        response = requests.post(
            API_URL,
            json={
                "apiKey": key,
                "modelName": model,
                "calledMethod": method,
                "methodProperties": props,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("novaposhta %s/%s failed: %s", model, method, exc)
        return []
    if not payload.get("success"):
        logger.warning("novaposhta %s/%s errors: %s", model, method, payload.get("errors"))
        return []
    data = payload.get("data") or []
    return data if isinstance(data, list) else []


def search_cities(query: str, *, limit: int = 8) -> list[dict[str, str]]:
    q = (query or "").strip()
    if len(q) < 2:
        return []
    if demo_mode():
        return _demo_cities(q, limit=limit)
    if not configured():
        return []

    cache_key = f"np:cities:{q.casefold()}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    rows = _post(
        "Address",
        "searchSettlements",
        {"CityName": q, "Limit": str(limit)},
    )
    items: list[dict[str, str]] = []
    for row in rows:
        addresses = row.get("Addresses") if isinstance(row, dict) else None
        if not isinstance(addresses, list):
            continue
        for item in addresses:
            if not isinstance(item, dict):
                continue
            ref = (item.get("DeliveryCity") or item.get("Ref") or "").strip()
            present = (item.get("Present") or item.get("MainDescription") or "").strip()
            if not ref or not present:
                continue
            items.append({"ref": ref, "name": present})
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break

    cache.set(cache_key, items, 60 * 60)
    return items


def _warehouse_kind(row: dict[str, Any]) -> str:
    category = (row.get("CategoryOfWarehouse") or "").strip().casefold()
    if "postomat" in category or "поштомат" in category:
        return "locker"
    return "branch"


def warehouses_for_city(city_ref: str, *, kind: str = "branch") -> list[dict[str, str]]:
    ref = (city_ref or "").strip()
    want = "locker" if kind == "locker" else "branch"
    if not ref:
        return []
    if demo_mode():
        return _demo_warehouses(ref, kind=want)
    if not configured():
        return []

    cache_key = f"np:wh:{ref}:{want}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    items: list[dict[str, str]] = []
    page = 1
    while page <= 20:
        rows = _post(
            "Address",
            "getWarehouses",
            {
                "CityRef": ref,
                "Page": str(page),
                "Limit": str(PAGE_SIZE),
            },
        )
        if not rows:
            break
        for row in rows:
            if not isinstance(row, dict):
                continue
            if _warehouse_kind(row) != want:
                continue
            description = (row.get("Description") or row.get("DescriptionRu") or "").strip()
            number = (row.get("Number") or "").strip()
            if not description:
                continue
            label = description if not number or number in description else f"№{number}: {description}"
            items.append(
                {
                    "ref": (row.get("Ref") or "").strip(),
                    "label": label,
                    "number": number,
                }
            )
        if len(rows) < PAGE_SIZE:
            break
        page += 1

    cache.set(cache_key, items, 60 * 60)
    return items


def find_warehouses(query: str, *, kind: str = "branch") -> dict[str, Any]:
    """Resolve city by first letters and return all matching warehouses."""
    cities = search_cities(query, limit=5)
    if not cities:
        return {"city": "", "city_ref": "", "items": []}
    city = cities[0]
    items = warehouses_for_city(city["ref"], kind=kind)
    return {"city": city["name"], "city_ref": city["ref"], "items": items, "cities": cities}


def search_streets(city_ref: str, query: str, *, limit: int = 20) -> list[dict[str, str]]:
    ref = (city_ref or "").strip()
    street_q, _house = split_street_query(query)
    if not ref or len(street_q) < 2:
        return []
    if demo_mode():
        return _demo_streets(ref, street_q, limit=limit)
    if not configured():
        return []

    cache_key = f"np:streets:{ref}:{street_q.casefold()}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    rows = _post(
        "Address",
        "getStreet",
        {
            "CityRef": ref,
            "FindByString": street_q,
            "Limit": str(limit),
        },
    )
    items: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        description = (row.get("Description") or "").strip()
        street_type = (row.get("StreetsType") or row.get("StreetType") or "").strip()
        street_ref = (row.get("Ref") or "").strip()
        if not description:
            continue
        label = f"{street_type} {description}".strip() if street_type else description
        items.append({"ref": street_ref, "label": label})
        if len(items) >= limit:
            break

    cache.set(cache_key, items, 60 * 30)
    return items
