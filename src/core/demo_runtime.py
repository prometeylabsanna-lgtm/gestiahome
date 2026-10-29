"""Cold-start helpers for the Vercel demo SQLite deploy."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def ensure_demo_superuser() -> bool:
    """Create/update demo superuser from env vars. Idempotent. Returns True if ensured."""
    username = (os.environ.get("DJANGO_SUPERUSER_USERNAME") or "").strip()
    email = (os.environ.get("DJANGO_SUPERUSER_EMAIL") or "").strip()
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD") or ""
    if not username or not password:
        return False

    from django.contrib.auth import get_user_model

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    changed = created
    if not user.is_staff or not user.is_superuser:
        user.is_staff = True
        user.is_superuser = True
        changed = True
    if email and user.email != email:
        user.email = email
        changed = True
    # Always set password when env provides one (cold start /tmp DB is fresh often).
    user.set_password(password)
    user.save()
    logger.info(
        "Demo superuser %s (%s)",
        username,
        "created" if created else "updated",
    )
    return True
