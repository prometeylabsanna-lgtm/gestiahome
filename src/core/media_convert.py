"""JPEG/PNG у полях зображень → WebP. Оригінал лишається в резервній теці."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path, PurePosixPath

from django.apps import apps
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from src.core.images import encode_upload

BACKUP_PREFIX = "_originals_backup"
_CONVERT_SUFFIXES = {".jpg", ".jpeg", ".png"}
_UNSAFE = (SuspiciousFileOperation, ValueError, OSError)


@dataclass
class ImageRef:
    model: type[models.Model]
    pk: int
    field_name: str
    storage: object
    name: str


@dataclass
class ConvertReport:
    apply: bool = False
    converted: int = 0
    references: int = 0
    already: int = 0
    skipped: int = 0
    missing: int = 0
    unsafe: int = 0
    errors: int = 0
    backups: int = 0
    details: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def convert_stored_images(*, apply: bool = False, today: str | None = None) -> ConvertReport:
    day = today or timezone.localdate().isoformat()
    report = ConvertReport(apply=apply)
    groups: dict[tuple[str, str], list[ImageRef]] = {}
    for ref in iter_image_refs():
        groups.setdefault((_storage_location(ref.storage), ref.name), []).append(ref)
    taken = {ref.name for grouped in groups.values() for ref in grouped}
    for key in sorted(groups, key=lambda item: item[1]):
        _convert_group(groups[key], taken, day, report)
    return report


def iter_image_refs():
    for model in apps.get_models():
        opts = model._meta
        if opts.proxy or opts.swapped or not opts.managed:
            continue
        image_fields = [
            item for item in opts.local_concrete_fields if isinstance(item, models.ImageField)
        ]
        if not image_fields:
            continue
        columns = [item.attname for item in image_fields]
        for row in model.objects.values_list("pk", *columns):
            for image_field, value in zip(image_fields, row[1:]):
                name = str(value or "").strip()
                if not name:
                    continue
                yield ImageRef(model, row[0], image_field.attname, image_field.storage, name)


def format_report(report: ConvertReport) -> str:
    converted_label = "Конвертовано" if report.apply else "Буде конвертовано"
    lines = [
        f"Режим: {'запис' if report.apply else 'перегляд'}",
        f"{converted_label}: {report.converted}",
        f"Полів у базі: {report.references}",
        f"Вже WebP: {report.already}",
        f"Інший формат: {report.skipped}",
        f"Немає файлу: {report.missing}",
        f"Небезпечна адреса: {report.unsafe}",
        f"Помилки: {report.errors}",
        f"Резервних копій: {report.backups}",
        *report.details,
        (
            f"converted={report.converted} references={report.references} "
            f"already={report.already} skipped={report.skipped} missing={report.missing} "
            f"unsafe={report.unsafe} errors={report.errors} backups={report.backups} "
            f"apply={int(report.apply)}"
        ),
    ]
    return "\n".join(lines)


def is_static_tree(path: Path) -> bool:
    resolved = path.resolve()
    roots = [Path(settings.BASE_DIR) / "src" / "core" / "static"]
    static_root = getattr(settings, "STATIC_ROOT", "")
    if static_root:
        roots.append(Path(static_root))
    for root in roots:
        try:
            resolved.relative_to(Path(root).resolve())
        except ValueError:
            continue
        return True
    return False


def _convert_group(refs: list[ImageRef], taken: set[str], day: str, report: ConvertReport) -> None:
    ref = refs[0]
    storage = ref.storage
    name = ref.name
    if _is_backup_name(name):
        report.skipped += 1
        return
    located = _locate(storage, name)
    if located is not None and is_static_tree(located):
        report.unsafe += 1
        report.problems.append(f"{name}: unsafe")
        return
    if not _exists(storage, name) and located is None:
        report.missing += 1
        return
    if located is not None and not located.is_file() and not _exists(storage, name):
        report.missing += 1
        return
    suffix = PurePosixPath(name).suffix.lower()
    if suffix == ".webp":
        report.already += 1
        return
    if suffix not in _CONVERT_SUFFIXES:
        report.skipped += 1
        return
    try:
        payload = _read_bytes(storage, name, located)
        content = encode_upload(BytesIO(payload), name)
    except Exception as exc:
        report.errors += 1
        report.problems.append(f"{name}: {type(exc).__name__}")
        return
    if content is None:
        report.errors += 1
        report.problems.append(f"{name}: encode")
        return
    target = _plan_target(storage, name, taken, apply=report.apply)
    saved = target
    backup_state = ""
    if report.apply:
        backup_state = _write_backup(storage, name, payload, day)
        if backup_state == "failed":
            report.errors += 1
            report.problems.append(f"{name}: backup")
            return
        try:
            content.seek(0)
            saved = storage.save(target, content)
            _update_refs(refs, saved)
        except Exception as exc:
            report.errors += 1
            report.problems.append(f"{name}: {type(exc).__name__}")
            return
        _delete_source(storage, name, saved, report)
        if backup_state == "new":
            report.backups += 1
        taken.add(saved)
        for item in refs:
            taken.discard(item.name)
    labels = ", ".join(f"{item.model._meta.label}.{item.field_name}" for item in refs)
    prefix = "" if report.apply else "перегляд "
    report.details.append(f"{prefix}{labels}: {name} → {saved}")
    report.converted += 1
    report.references += len(refs)


def _update_refs(refs: list[ImageRef], new_name: str) -> None:
    with transaction.atomic():
        for ref in refs:
            updated = ref.model.objects.filter(pk=ref.pk).update(**{ref.field_name: new_name})
            if updated != 1:
                raise LookupError(ref.field_name)


def _delete_source(storage, name: str, new_name: str, report: ConvertReport) -> None:
    if name == new_name:
        return
    try:
        if storage.exists(name):
            storage.delete(name)
    except Exception as exc:
        report.problems.append(f"{name}: delete {type(exc).__name__}")


def _write_backup(storage, name: str, payload: bytes, day: str) -> str:
    relative = f"{BACKUP_PREFIX}/{day}/{name.replace(chr(92), '/').lstrip('/')}"
    # Local FS: keep path traversal guard. S3 / remote: storage API only.
    located = _locate(storage, relative)
    if located is not None:
        if located.is_file() and located.stat().st_size > 0:
            return "kept"
        try:
            located.parent.mkdir(parents=True, exist_ok=True)
            located.write_bytes(payload)
        except OSError:
            return "failed"
        if located.is_file() and located.stat().st_size == len(payload):
            return "new"
        return "failed"
    try:
        if _exists(storage, relative):
            return "kept"
        storage.save(relative, ContentFile(payload))
        return "new"
    except Exception:
        return "failed"


def _read_bytes(storage, name: str, located: Path | None) -> bytes:
    if located is not None and located.is_file():
        return located.read_bytes()
    with storage.open(name, "rb") as handle:
        return handle.read()


def _plan_target(storage, name: str, taken: set[str], *, apply: bool) -> str:
    base = PurePosixPath(name).with_suffix(".webp").as_posix()
    candidate = base
    for index in range(2, 30):
        blocked = candidate in taken
        exists = _exists(storage, candidate)
        if not blocked and not exists:
            return candidate
        if not blocked and exists:
            if apply:
                storage.delete(candidate)
            return candidate
        stem = PurePosixPath(base).with_suffix("").as_posix()
        candidate = f"{stem}--{index}.webp"
    stem = PurePosixPath(base).with_suffix("").as_posix()
    return f"{stem}--{get_random_string(6)}.webp"


def _locate(storage, name: str) -> Path | None:
    try:
        path = Path(storage.path(name)).resolve()
    except _UNSAFE:
        return None
    root = Path(settings.MEDIA_ROOT).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def _exists(storage, name: str) -> bool:
    try:
        return bool(storage.exists(name))
    except _UNSAFE:
        return False


def _is_backup_name(name: str) -> bool:
    parts = PurePosixPath(name.replace("\\", "/")).parts
    return bool(parts) and parts[0] == BACKUP_PREFIX


def _storage_location(storage) -> str:
    try:
        return str(Path(storage.location).resolve())
    except Exception:
        pass
    bucket = getattr(storage, "bucket_name", None) or getattr(
        settings, "AWS_STORAGE_BUCKET_NAME", ""
    )
    if bucket:
        return f"s3:{bucket}"
    return storage.__class__.__module__ + "." + storage.__class__.__name__
