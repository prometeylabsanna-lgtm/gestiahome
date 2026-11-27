from __future__ import annotations

import re

from django.db.models import Case, IntegerField, Q, Value, When

from src.commerce.np_models import NovaPoshtaCity, NovaPoshtaWarehouse
from src.commerce.novaposhta import DEMO_CITIES, DEMO_LOCKERS, DEMO_WAREHOUSES

SUGGEST_LIMIT = 30
_SPACE_RE = re.compile(r"\s+")
_EN = "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
_UK = "йцукенгшщзхїфівапролджєячсмитьбю.ґ"
_TO_UK = str.maketrans(_EN, _UK)
_TO_EN = str.maketrans(_UK, _EN)


def build_search_text(*parts: str) -> str:
    raw = " ".join(part.strip() for part in parts if part and str(part).strip())
    return _SPACE_RE.sub(" ", raw.casefold()).strip()


def normalize_query(query: str) -> str:
    text = (query or "").replace("№", " ")
    text = text.strip().casefold()
    return _SPACE_RE.sub(" ", text).strip()


def layout_variants(query: str) -> list[str]:
    base = normalize_query(query)
    if len(base) < 2:
        return []
    variants = [base]
    for item in (base.translate(_TO_UK), base.translate(_TO_EN)):
        if item not in variants:
            variants.append(item)
    return variants


def has_cities() -> bool:
    return NovaPoshtaCity.objects.exists()


def has_warehouses() -> bool:
    return NovaPoshtaWarehouse.objects.exists()


def search_cities(query: str, *, limit: int = 12) -> list[dict[str, str]]:
    variants = layout_variants(query)
    if not variants:
        return []
    limit = max(1, min(int(limit), 20))
    primary = variants[0]
    text_q = Q()
    for variant in variants:
        text_q |= Q(search_text__contains=variant)
    rows = (
        NovaPoshtaCity.objects.filter(text_q)
        .annotate(
            rank=Case(
                When(search_text__startswith=primary, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("rank", "name")[:limit]
    )
    return [{"ref": row.ref, "name": row.name} for row in rows]


def search_warehouses(
    query: str,
    *,
    city_ref: str = "",
    kind: str = "branch",
    limit: int = SUGGEST_LIMIT,
) -> list[dict[str, str]]:
    variants = layout_variants(query)
    if not variants:
        return []
    limit = max(1, min(int(limit), SUGGEST_LIMIT))
    want = "locker" if kind == "locker" else "branch"
    city_ref = (city_ref or "").strip()
    if not has_warehouses():
        return _search_demo(variants, city_ref=city_ref, kind=want, limit=limit)
    return _search_db(variants, city_ref=city_ref, kind=want, limit=limit)


def resolve_warehouse(ref: str, *, kind: str, city_ref: str = "") -> dict[str, str] | None:
    ref = (ref or "").strip()
    if not ref:
        return None
    want = "locker" if kind == "locker" else "branch"
    city_ref = (city_ref or "").strip()
    if has_warehouses():
        row = NovaPoshtaWarehouse.objects.filter(ref=ref, is_active=True, kind=want).first()
        if row is None:
            return None
        if city_ref and row.city_ref != city_ref:
            return None
        return {
            "ref": row.ref,
            "label": row.label,
            "number": row.number,
            "city_ref": row.city_ref,
            "city_name": row.city_name,
        }
    return _resolve_demo(ref, kind=want, city_ref=city_ref)


def _search_db(variants: list[str], *, city_ref: str, kind: str, limit: int) -> list[dict[str, str]]:
    primary = variants[0]
    text_q = Q()
    for variant in variants:
        text_q |= Q(search_text__contains=variant)
        digits = variant.replace(" ", "")
        if digits.isdigit():
            text_q |= Q(number__startswith=digits)
    qs = NovaPoshtaWarehouse.objects.filter(is_active=True, kind=kind).filter(text_q)
    if city_ref:
        qs = qs.filter(city_ref=city_ref)
    rows = qs.annotate(rank=_rank(primary)).order_by("rank", "number", "label")[:limit]
    return [_row_payload(row, with_city=not city_ref) for row in rows]


def _rank(primary: str) -> Case:
    digits = primary.replace(" ", "")
    whens = [
        When(search_text__startswith=primary, then=Value(2)),
        When(search_text__contains=primary, then=Value(3)),
    ]
    if digits.isdigit():
        whens.insert(0, When(number__startswith=digits, then=Value(1)))
        whens.insert(0, When(number__iexact=digits, then=Value(0)))
    return Case(*whens, default=Value(4), output_field=IntegerField())


def _row_payload(row: NovaPoshtaWarehouse, *, with_city: bool) -> dict[str, str]:
    return {
        "ref": row.ref,
        "label": row.label,
        "caption": _caption(row.label, row.city_name, with_city=with_city),
        "number": row.number,
        "city_ref": row.city_ref,
        "city_name": row.city_name,
    }


def _caption(label: str, city_name: str, *, with_city: bool) -> str:
    if not with_city or not city_name:
        return label
    if city_name.casefold() in label.casefold():
        return label
    return f"{label} — {city_name}"


def _search_demo(variants: list[str], *, city_ref: str, kind: str, limit: int) -> list[dict[str, str]]:
    source = DEMO_LOCKERS if kind == "locker" else DEMO_WAREHOUSES
    city_names = {row["ref"]: row["name"] for row in DEMO_CITIES}
    found: list[tuple[int, dict[str, str], str, str]] = []
    for ref, items in source.items():
        if city_ref and ref != city_ref:
            continue
        city_name = city_names.get(ref, "")
        for item in items:
            text = build_search_text(item.get("number", ""), item.get("label", ""), city_name)
            if not _demo_matches(item, text, variants):
                continue
            found.append((_demo_rank(item, text, variants[0]), item, ref, city_name))
    found.sort(key=lambda row: (row[0], row[1].get("number", ""), row[1].get("label", "")))
    return [
        _demo_payload(item, city_ref=ref, city_name=city_name, with_city=not city_ref)
        for _rank, item, ref, city_name in found[:limit]
    ]


def _demo_matches(item: dict[str, str], text: str, variants: list[str]) -> bool:
    number = str(item.get("number", ""))
    for variant in variants:
        if variant in text:
            return True
        digits = variant.replace(" ", "")
        if digits.isdigit() and number.startswith(digits):
            return True
    return False


def _demo_rank(item: dict[str, str], text: str, primary: str) -> int:
    number = str(item.get("number", ""))
    digits = primary.replace(" ", "")
    if digits.isdigit() and number.casefold() == digits:
        return 0
    if digits.isdigit() and number.startswith(digits):
        return 1
    if text.startswith(primary):
        return 2
    if primary in text:
        return 3
    return 4


def _demo_payload(item: dict[str, str], *, city_ref: str, city_name: str, with_city: bool) -> dict[str, str]:
    label = item.get("label", "")
    return {
        "ref": item.get("ref", ""),
        "label": label,
        "caption": _caption(label, city_name, with_city=with_city),
        "number": item.get("number", ""),
        "city_ref": city_ref,
        "city_name": city_name,
    }


def _resolve_demo(ref: str, *, kind: str, city_ref: str) -> dict[str, str] | None:
    source = DEMO_LOCKERS if kind == "locker" else DEMO_WAREHOUSES
    city_names = {row["ref"]: row["name"] for row in DEMO_CITIES}
    for demo_city, items in source.items():
        for item in items:
            if item.get("ref") != ref:
                continue
            if city_ref and demo_city != city_ref:
                return None
            return {
                "ref": ref,
                "label": item.get("label", ""),
                "number": item.get("number", ""),
                "city_ref": demo_city,
                "city_name": city_names.get(demo_city, ""),
            }
    return None
