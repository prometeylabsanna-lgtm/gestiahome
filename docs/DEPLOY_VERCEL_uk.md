# Деплой Gestia на Vercel (демо / free tier)

Безкоштовний тест/демо: **без Postgres**. Сайт піднімається на committed SQLite + media у CDN. Записи в БД і завантаження файлів **не зберігаються** між cold start.

## Обмеження демо (прочитайте перед деплоєм)

| Тема | Поведінка |
|------|-----------|
| БД | `demo/gestia_demo.sqlite3` копіюється в `/tmp/gestia_demo.sqlite3` на cold start |
| Записи | Замовлення, правки в адмінці, зміни контенту зникають після cold start / redeploy |
| Media (каталог) | `demo/media` → `public/media` на build → CDN `/media/…` |
| Uploads у runtime | Пишуться в `/tmp/media` (ефемерні, CDN їх не віддає надійно) |
| Background | Немає Celery / cron / постійних воркерів |
| Function size | Python bundle ≤ ~500 MB unzipped; media **не** входить у function (`excludeFiles`) |
| Cold start | Копія SQLite (+ опційний `ensure_demo_superuser`) на старті інстансу |

Оновлення до продакшену: додайте `DATABASE_URL` (Neon/Postgres) і `AWS_STORAGE_BUCKET_NAME` (S3/R2) — код уже підтримує обидва шляхи.

## Змінні оточення (лише імена)

### Обовʼязкові

| Імʼя | Навіщо |
|------|--------|
| `SECRET_KEY` | Django secret. **Лише в Vercel Env UI.** На build без ключа — тимчасовий dummy; на runtime без ключа — помилка. |

### Рекомендовані для демо

| Імʼя | Навіщо |
|------|--------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.vercel` (або покладіться на `VERCEL=1` у `manage.py` / `wsgi.py`) |
| `SITE_URL` | Canonical / sitemap (напр. `https://your-app.vercel.app`) |
| `ALLOWED_HOSTS` | Додаткові хости (`.vercel.app` уже додається в settings) |
| `CSRF_TRUSTED_ORIGINS` | Додаткові `https://…` origins |
| `ADMIN_URL` | Префікс адмінки (default `admin/`) |
| `DJANGO_SUPERUSER_USERNAME` | Опційно: логін демо-адміна (створюється на кожному cold start у `/tmp`) |
| `DJANGO_SUPERUSER_EMAIL` | Email суперкористувача |
| `DJANGO_SUPERUSER_PASSWORD` | Пароль (ніколи не комітити) |

### Опційно (апгрейд)

| Імʼя | Навіщо |
|------|--------|
| `DATABASE_URL` | Postgres (Neon тощо). Якщо задано — demo SQLite **не** використовується |
| `AWS_STORAGE_BUCKET_NAME` | Persistent media через django-storages S3 |
| `AWS_S3_ENDPOINT_URL` | R2 / Spaces endpoint |
| `AWS_S3_CUSTOM_DOMAIN` | CDN-домен бакета |
| `AWS_S3_REGION_NAME` | Регіон |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Ключі S3-сумісного API |
| `SECURE_SSL_REDIRECT` | Default `True` на vercel settings |
| `SECURE_HSTS_SECONDS` | HSTS |
| `DEFAULT_FROM_EMAIL` / `ORDER_NOTIFY_EMAIL` / Telegram / Nova Poshta | Як у `.env.example` (на демо сповіщення ненадійні) |

Системні (виставляє Vercel): `VERCEL`, `VERCEL_URL`, `VERCEL_ENV`, `VERCEL_PROJECT_PRODUCTION_URL`, `CI` (лише build).

## Налаштування в Vercel UI

1. **Framework Preset:** Django (або автодетект через `manage.py`).
2. **Root Directory:** `.` (корінь репо).
3. **Build Command:**  
   `DJANGO_BUILD_PHASE=1 DJANGO_SETTINGS_MODULE=config.settings.vercel python build_vercel.py`  
   (уже в `vercel.json`; Vercel сам робить `collectstatic`, якщо є `STATIC_ROOT`).
4. **Install Command:** `pip install -r requirements.txt` (default).
5. **Python Version:** `3.12` (файл `.python-version`).
6. **Env:** додайте щонайменше `SECRET_KEY` для Production + Preview.
7. Не комітьте й не вставляйте секрети в `vercel.json`.

`compilemessages` **не** запускаємо на Vercel (немає gettext) — `.mo` уже в `locale/`.

## Локальна підготовка демо-артефактів

```bash
# з кореня репо, з робочою dev-БД і media/
DJANGO_SETTINGS_MODULE=config.settings.develop python manage.py build_demo_db
```

Команда:

1. Копіює `db.sqlite3` → `demo/gestia_demo.sqlite3`
2. Видаляє `auth_user*`, groups, sessions, admin log, `commerce_order*`, `commerce_inquiry`
3. Копіює лише файли, на які є посилання в БД, у `demo/media/` (без `_originals_backup`)

Перегенеруйте й закомітьте перед демо-деплоєм, якщо контент змінився.

## Media → CDN

`build_vercel.py` копіює `demo/media` → `public/media`. Запити `/media/…` обслуговує CDN, не Python function. У `vercel.json` → `excludeFiles` прибрані `media/**`, `demo/media/**`, `public/**` з бандла функції.

### Синхронізація на S3/R2 (після апгрейду)

```bash
# приклад: AWS CLI / rclone (підставте свої значення)
aws s3 sync ./media s3://YOUR_BUCKET/ \
  --endpoint-url https://YOUR_ENDPOINT \
  --exclude "_originals_backup/*"

# або
rclone sync ./media remote:YOUR_BUCKET --exclude "_originals_backup/**"
```

## Міграції / суперкористувач

На **демо SQLite** міграції вже всередині committed файлу — `migrate` на Vercel не потрібен.

Якщо підключили Postgres:

```bash
vercel env pull .env.vercel   # не комітити
export DJANGO_SETTINGS_MODULE=config.settings.vercel
# підвантажте змінні з .env.vercel без друку секретів
python manage.py migrate
python manage.py createsuperuser
```

Демо-адмін без Postgres (ефемерний):

- задайте `DJANGO_SUPERUSER_*` у Vercel Env;
- на cold start `config/wsgi.py` викликає `ensure_demo_superuser`;
- або вручну: `python manage.py ensure_demo_superuser`.

## Контент з dev у Postgres (майбутній апгрейд)

```bash
python manage.py dumpdata content catalog \
  --natural-foreign --natural-primary \
  -e contenttypes -e auth.permission \
  -e auth.user -e auth.group -e sessions \
  -e admin.logentry \
  -e commerce.order -e commerce.orderitem -e commerce.inquiry \
  -o /tmp/gestia_content.json

# УВАГА: виключіть proxy-моделі або дампте concrete labels
# (див. build_demo_db._concrete_labels у коді — для dumpdata краще concrete)

DJANGO_SETTINGS_MODULE=config.settings.vercel python manage.py loaddata /tmp/gestia_content.json
```

Для demo SQLite надійніше знову викликати `build_demo_db` (копія файлу БД).

## Troubleshooting: `[DJANGO_SETTINGS_FAILED] … SECRET_KEY`

**Було:** Vercel читає settings через `manage.py`, який за замовчуванням брав `config.settings.develop` → `base.SECRET_KEY = config("SECRET_KEY")` без default → `UndefinedValueError`.

**Стало:**

- при `VERCEL=1` default module = `config.settings.vercel`;
- `SECRET_KEY` у base з порожнім default;
- на build (`DJANGO_BUILD_PHASE=1` / `CI=1`) дозволений dummy key;
- на runtime без `SECRET_KEY` у Env — `ImproperlyConfigured`.

Перевірте, що в Env UI задано `SECRET_KEY` для потрібних environments і зроблено Redeploy.

## Швидка перевірка локально (без `.env`)

```bash
git worktree add /tmp/gestia_vc deploy/vercel
cd /tmp/gestia_vc
# без читання .env
env -i HOME="$HOME" PATH="$PATH" \
  VERCEL=1 CI=1 DJANGO_BUILD_PHASE=1 \
  DJANGO_SETTINGS_MODULE=config.settings.vercel \
  /path/to/.venv/bin/python -c "import django; django.setup(); print('ok')"
```
