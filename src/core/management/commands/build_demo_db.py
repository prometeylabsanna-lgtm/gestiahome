"""Build committed demo SQLite + copy referenced media for Vercel CDN."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Таблиці з PII / сесіями / замовленнями — прибираємо з demo DB.
PURGE_SQL = (
    "DELETE FROM commerce_orderitem;",
    "DELETE FROM commerce_order;",
    "DELETE FROM commerce_inquiry;",
    "DELETE FROM django_admin_log;",
    "DELETE FROM django_session;",
    "DELETE FROM auth_user_groups;",
    "DELETE FROM auth_user_user_permissions;",
    "DELETE FROM auth_group_permissions;",
    "DELETE FROM auth_group;",
    "DELETE FROM auth_user;",
)

MEDIA_FIELD_NAMES = frozenset(
    {
        "image",
        "image_mobile",
        "video",
        "logo",
        "card_image",
    }
)


class Command(BaseCommand):
    help = (
        "Створює demo/gestia_demo.sqlite3 (копія поточної SQLite без користувачів/"
        "замовлень/сесій) і копіює лише файли з посилань у demo/media/."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-db",
            default="",
            help="Шлях до джерельної SQLite (default: DATABASES default NAME).",
        )
        parser.add_argument(
            "--skip-media",
            action="store_true",
            help="Не копіювати media у demo/media/.",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        demo_dir = base_dir / "demo"
        demo_dir.mkdir(parents=True, exist_ok=True)
        target_db = demo_dir / "gestia_demo.sqlite3"
        media_root = Path(settings.MEDIA_ROOT)
        demo_media = demo_dir / "media"

        source_db = Path(options["source_db"] or settings.DATABASES["default"]["NAME"])
        if not source_db.is_file():
            raise CommandError(f"Source DB not found: {source_db}")

        if target_db.resolve() == source_db.resolve():
            raise CommandError("Refusing to overwrite the source database.")

        self.stdout.write(f"Copy {source_db} → {target_db}")
        if target_db.exists():
            target_db.unlink()
        shutil.copy2(source_db, target_db)
        self._purge_pii(target_db)
        self.stdout.write(self.style.SUCCESS(f"Wrote {target_db} (PII purged)"))

        if options["skip_media"]:
            return

        if demo_media.exists():
            shutil.rmtree(demo_media)
        demo_media.mkdir(parents=True)

        names = self._media_names_from(target_db)
        copied = 0
        missing = 0
        oversized: list[str] = []
        for relative in sorted(names):
            src = media_root / relative
            if not src.is_file():
                missing += 1
                self.stderr.write(f"missing: {relative}")
                continue
            size_mb = src.stat().st_size / (1024 * 1024)
            if size_mb > 50:
                oversized.append(f"{relative} ({size_mb:.1f} MB)")
            dest = demo_media / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            copied += 1

        self.stdout.write(
            self.style.SUCCESS(f"demo/media: copied={copied} missing={missing}")
        )
        for item in oversized:
            self.stderr.write(self.style.WARNING(f">50MB: {item}"))

    def _purge_pii(self, db_path: Path) -> None:
        conn = sqlite3.connect(str(db_path))
        try:
            existing = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            for statement in PURGE_SQL:
                table = statement.split()[2].rstrip(";")
                if table in existing:
                    conn.execute(statement)
            conn.commit()
            conn.execute("VACUUM")
        finally:
            conn.close()

    def _media_names_from(self, db_path: Path) -> set[str]:
        names: set[str] = set()
        conn = sqlite3.connect(str(db_path))
        try:
            tables = [
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            ]
            for table in tables:
                cols = [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')]
                media_cols = [c for c in cols if c in MEDIA_FIELD_NAMES]
                if not media_cols:
                    continue
                select = ", ".join(f'"{c}"' for c in media_cols)
                for row in conn.execute(f'SELECT {select} FROM "{table}"'):
                    for value in row:
                        text = str(value or "").strip()
                        if text and not text.startswith("http"):
                            names.add(text.replace("\\", "/").lstrip("/"))
        finally:
            conn.close()
        return names
