from __future__ import annotations

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from src.commerce.np_catalog import build_search_text
from src.commerce.np_models import NovaPoshtaCity, NovaPoshtaSyncState, NovaPoshtaWarehouse
from src.commerce.novaposhta import PAGE_SIZE, NovaPoshtaError, configured, post_rows

logger = logging.getLogger(__name__)

MAX_PAGES = 200
_SKIP_MESSAGE = (
    "Ключ NOVA_POSHTA_API_KEY порожній. Додайте його в .env і запустіть: "
    "python manage.py sync_nova_poshta"
)


def sync_catalog() -> dict[str, Any]:
    if not configured():
        return {"skipped": True, "message": _SKIP_MESSAGE}
    batches = _fetch_pages()
    rows = _collect(batches)
    if not rows:
        raise NovaPoshtaError("Нова пошта повернула порожній каталог")
    counts = _store(rows)
    logger.info(
        "novaposhta catalog synced warehouses=%s cities=%s",
        counts["warehouses"],
        counts["cities"],
    )
    return {"skipped": False, **counts}


def _fetch_pages() -> list[list[dict[str, Any]]]:
    batches: list[list[dict[str, Any]]] = []
    page = 1
    while page <= MAX_PAGES:
        batch = post_rows(
            "Address",
            "getWarehouses",
            {"Page": str(page), "Limit": str(PAGE_SIZE)},
        )
        batches.append(batch)
        if len(batch) < PAGE_SIZE:
            return batches
        page += 1
    raise NovaPoshtaError("Каталог Нової пошти не вмістився в ліміт сторінок")


def _collect(batches: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    by_ref: dict[str, dict[str, Any]] = {}
    for batch in batches:
        for raw in batch:
            item = _parse(raw)
            if item is not None:
                by_ref[item["ref"]] = item
    return list(by_ref.values())


def _parse(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    ref = (raw.get("Ref") or "").strip()
    label = (raw.get("Description") or raw.get("DescriptionRu") or "").strip()
    if not ref or not label:
        return None
    number = str(raw.get("Number") or "").strip()[:16]
    city_name = (raw.get("CityDescription") or raw.get("SettlementDescription") or "").strip()
    area = (raw.get("SettlementAreaDescription") or "").strip()
    if area and area.casefold() not in city_name.casefold():
        city_name = f"{city_name}, {area}"
    address = (raw.get("ShortAddress") or "").strip()
    status = (raw.get("WarehouseStatus") or "").strip().casefold()
    return {
        "ref": ref[:64],
        "number": number,
        "label": label[:400],
        "city_ref": (raw.get("CityRef") or "").strip()[:64],
        "city_name": city_name[:180],
        "area": area[:160],
        "address": address[:400],
        "kind": _kind(raw),
        "is_active": status in {"", "working"},
        "search_text": build_search_text(number, label, address, city_name)[:900],
    }


def _kind(raw: dict[str, Any]) -> str:
    category = (raw.get("CategoryOfWarehouse") or "").casefold()
    description = (raw.get("Description") or "").casefold()
    if "postomat" in category or "поштомат" in category:
        return NovaPoshtaWarehouse.Kind.LOCKER
    if "postomat" in description or "поштомат" in description:
        return NovaPoshtaWarehouse.Kind.LOCKER
    return NovaPoshtaWarehouse.Kind.BRANCH


def _store(rows: list[dict[str, Any]]) -> dict[str, int]:
    warehouses = [
        NovaPoshtaWarehouse(
            ref=row["ref"],
            number=row["number"],
            label=row["label"],
            city_ref=row["city_ref"],
            city_name=row["city_name"],
            address=row["address"],
            kind=row["kind"],
            is_active=row["is_active"],
            search_text=row["search_text"],
        )
        for row in rows
    ]
    cities = _cities(rows)
    with transaction.atomic():
        NovaPoshtaWarehouse.objects.update(is_active=False)
        NovaPoshtaWarehouse.objects.bulk_create(
            warehouses,
            batch_size=PAGE_SIZE,
            update_conflicts=True,
            unique_fields=["ref"],
            update_fields=[
                "number",
                "label",
                "city_ref",
                "city_name",
                "address",
                "kind",
                "is_active",
                "search_text",
            ],
        )
        NovaPoshtaCity.objects.all().delete()
        NovaPoshtaCity.objects.bulk_create(cities, batch_size=PAGE_SIZE)
        state, _created = NovaPoshtaSyncState.objects.get_or_create(pk=1)
        state.last_synced_at = timezone.now()
        state.warehouse_count = len(warehouses)
        state.city_count = len(cities)
        state.save(update_fields=["last_synced_at", "warehouse_count", "city_count"])
    return {"warehouses": len(warehouses), "cities": len(cities)}


def _cities(rows: list[dict[str, Any]]) -> list[NovaPoshtaCity]:
    by_ref: dict[str, NovaPoshtaCity] = {}
    for row in rows:
        ref = row["city_ref"]
        name = row["city_name"]
        if not ref or not name:
            continue
        by_ref[ref] = NovaPoshtaCity(
            ref=ref,
            name=name,
            area=row["area"],
            search_text=build_search_text(name, row["area"])[:360],
        )
    return list(by_ref.values())
