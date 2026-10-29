# Деплой Gestia на Vercel (демо / free tier)

Безкоштовний тест/демо: **без Postgres** і **без обовʼязкових env vars**. Сайт піднімається на committed SQLite + media у CDN. Записи в БД і завантаження файлів **не зберігаються** між cold start.

## Обмеження демо (прочитайте перед деплоєм)

| Тема | Поведінка |
|------|-----------|
| БД | `demo/gestia_demo.sqlite3` копіюється в `/tmp/gestia_demo.sqlite3` на cold start |
| Записи | Замовлення, правки в адмінці, зміни контенту зникають після cold start / redeploy |
| Media (каталог) | `demo/media` (~44 MB) у бандлі функції; WhiteNoise віддає `/media/…`. На build також копія в `public/media` |
| Uploads у runtime | Пишуться в `/tmp/media` (ефемерні, WhiteNoise їх не бачить) |
| Background | Немає Celery / cron / постійних воркерів |
| Function size | Python bundle ≤ ~500 MB unzipped; media **не** входить у function (`excludeFiles`) |
| Cold start | Копія SQLite в `/tmp` (без авто-створення суперкористувача) |
| Секрет | У коді є публічний `DEMO_SECRET_KEY` — **демо не повинно тримати реальні дані** |
| Адмін | У demo DB **немає** admin-користувача; як його отримати для демо — поза межами цього гайду / майбутнє |

Оновлення до продакшену: додайте `DATABASE_URL` (Neon/Postgres) і `AWS_STORAGE_BUCKET_NAME` (S3/R2) — код уже підтримує обидва шляхи. Для реального прод **обовʼязково** свій `SECRET_KEY` (і `config.settings.production`, не demo-ключ).

## Змінні оточення

**Для демо на Vercel з нульовими Env — нічого задавати не потрібно.**  
`config.settings.vercel` підставляє demo `SECRET_KEY`, хости `.vercel.app` / localhost, CSRF `https://*.vercel.app`, `ADMIN_URL=admin/`. Системні `VERCEL_*` підхоплюються автоматично.

### Опційно (майбутній реальний prod / розширене демо)

| Імʼя | Навіщо |
|------|--------|
| `SECRET_KEY` | Власний Django secret замість публічного `DEMO_SECRET_KEY` (**обовʼязково** для будь-яких реальних даних) |
| `DJANGO_SETTINGS_MODULE` | `config.settings.vercel` (або покладіться на `VERCEL=1` у `manage.py` / `wsgi.py`) |
| `SITE_URL` | Canonical / sitemap; інакше `https://` + `VERCEL_PROJECT_PRODUCTION_URL` / `VERCEL_URL`, або host із request |
| `ALLOWED_HOSTS` | Додаткові хости (`.vercel.app`, `localhost`, `127.0.0.1` уже в settings) |
| `CSRF_TRUSTED_ORIGINS` | Додаткові `https://…` (`https://*.vercel.app` уже є) |
| `ADMIN_URL` | Префікс адмінки (default `admin/` — env не потрібен) |
| `DATABASE_URL` | Postgres (Neon тощо). Якщо задано — demo SQLite **не** використовується |
| `AWS_STORAGE_BUCKET_NAME` | Persistent media через django-storages S3 |
| `AWS_S3_ENDPOINT_URL` | R2 / Spaces endpoint |
| `AWS_S3_CUSTOM_DOMAIN` | CDN-домен бакета |
| `AWS_S3_REGION_NAME` | Регіон |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Ключі S3-сумісного API |
| `SECURE_SSL_REDIRECT` | Default `True` на vercel settings |
| `SECURE_HSTS_SECONDS` | HSTS |
| `DJANGO_SUPERUSER_USERNAME` / `EMAIL` / `PASSWORD` | Лише для ручної команди `ensure_demo_superuser` (на cold start **не** викликається) |
| `DEFAULT_FROM_EMAIL` / `ORDER_NOTIFY_EMAIL` / Telegram / Nova Poshta | Як у `.env.example` (на демо сповіщення ненадійні) |

Системні (виставляє Vercel): `VERCEL`, `VERCEL_URL`, `VERCEL_ENV`, `VERCEL_PROJECT_PRODUCTION_URL`, `VERCEL_BRANCH_URL`, `CI` (лише build).

## Налаштування в Vercel UI

1. **Framework Preset:** Django (або автодетект через `manage.py`).
2. **Root Directory:** `.` (корінь репо).
3. **Build Command:**  
   `DJANGO_BUILD_PHASE=1 DJANGO_SETTINGS_MODULE=config.settings.vercel python build_vercel.py`  
   (уже в `vercel.json`; Vercel сам робить `collectstatic`, якщо є `STATIC_ROOT`).
4. **Install Command:** `pip install -r requirements.txt` (default).
5. **Python Version:** `3.12` (файл `.python-version`).
6. **Env:** для демо-проєкту можна лишити **порожнім**.
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

## Media

- **Читання демо-файлів:** `config/wsgi.py` обгортає app у WhiteNoise з `demo/media` → URL `/media/…`. Тому `demo/media` **входить** у function bundle (~44 MB; ліміт Python ~500 MB).
- **Build:** `build_vercel.py` також копіює в `public/media` (на випадок CDN-віддачі платформою).
- **excludeFiles:** прибирає важкий `/media` (dev), `public/`, docs/figma, sqlite backups — не `demo/media`.
- **Uploads** без S3 → `/tmp/media`, ефемерні.

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

У demo DB є суперкористувач **admin / admin** (зашитий у `demo/gestia_demo.sqlite3` під час `build_demo_db`). Cold start не створює інших користувачів. Команда `python manage.py ensure_demo_superuser` лишається для опційного оверрайду через `DJANGO_SUPERUSER_*`.

Сесії адмінки на Vercel — `signed_cookies` (не SQLite у `/tmp`), інакше логін «відлітає» на кожному переході між serverless-інстансами.

Якщо підключили Postgres:

```bash
vercel env pull .env.vercel   # не комітити
export DJANGO_SETTINGS_MODULE=config.settings.vercel
# підвантажте змінні з .env.vercel без друку секретів
python manage.py migrate
python manage.py createsuperuser
```

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

## Troubleshooting: settings / SECRET_KEY

- при `VERCEL=1` default module = `config.settings.vercel`;
- `SECRET_KEY` у base з порожнім default (імпорт не падає);
- на vercel без env — публічний `DEMO_SECRET_KEY` (лише демо!);
- `config.settings.production` як і раніше **вимагає** `SECRET_KEY`.

## Швидка перевірка локально (без `.env`)

```bash
git worktree add /tmp/gestia_vc2 HEAD
cd /tmp/gestia_vc2
env -i HOME="$HOME" PATH="$PATH" VERCEL=1 \
  ~/Sites/Gestia/.venv/bin/python -c \
  "import os,django;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.vercel');django.setup();from django.conf import settings;print(bool(settings.SECRET_KEY), settings.DEBUG, settings.ALLOWED_HOSTS[:3])"
# далі: manage.py check + test-client GET / і /katalog/ з HTTP_HOST=…vercel.app
git worktree remove /tmp/gestia_vc2
```
