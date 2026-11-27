# Gestia на DigitalOcean Droplet

Один спосіб деплою: Docker Compose. Host nginx / systemd gunicorn на :80/:443 не вмикати.

Файли `deploy/systemd/gunicorn.service` і `deploy/nginx/gestia.conf` — запасний контур, не для цього Droplet.

## Передумови

- Ubuntu 24.04, 2 GB RAM (магазин)
- Шлях: `/var/www/gestia`
- Firewall: `ufw allow OpenSSH`, `ufw allow 80/tcp`, `ufw allow 443/tcp`
- `.env` лише на сервері, не в git

## HTTP по IP

```bash
mkdir -p /var/www && cd /var/www
git clone <REPO> gestia
cd /var/www/gestia
bash deploy/docker/install-docker.sh
cp .env.docker.example .env
nano .env
```

У `.env`: `SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL` з тим самим паролем, `ADMIN_URL` не `admin/`, `ALLOWED_HOSTS` — реальний IPv4 + `127.0.0.1,localhost,backend`. Не лишай літерал `DROPLET_IP`.

HTTP-тест: `SESSION_COOKIE_SECURE=False`, `CSRF_COOKIE_SECURE=False`, `USE_HTTPS=false`.

```bash
bash deploy/docker/deploy.sh
curl -sf http://127.0.0.1/healthz/
```

Перенести вітрину з ноутбука (без користувачів і демо-admin):

```bash
# локально
./deploy/docker/sync-data.sh export
# скопіювати deploy/data/shop.json і media.tar.gz на сервер, потім:
./deploy/docker/sync-data.sh load
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

`createsuperuser` — після `load`. Демо `admin/admin` не імпортується.

## DNS і SSL

A `@` і `www` → IP Droplet. Дочекатися propagation.

```bash
apt install -y certbot
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop nginx
certbot certonly --standalone -d example.com -d www.example.com --agree-tos -m you@example.com
```

У `.env`: `DOMAIN=example.com` (перший `-d` certbot), `USE_HTTPS=true`, `SITE_URL=https://example.com`, `CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com`, домен і www у `ALLOWED_HOSTS`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`.

```bash
bash deploy/docker/deploy.sh
curl -sfk https://127.0.0.1/healthz/
```

TLS завершується в nginx. `SECURE_SSL_REDIRECT` у Gunicorn лишається вимкненим.

## Renew

```bash
PROJECT=/var/www/gestia
COMPOSE="docker compose -f $PROJECT/docker-compose.yml -f $PROJECT/docker-compose.prod.yml -f $PROJECT/docker-compose.ssl.yml"

cat > /etc/letsencrypt/renewal-hooks/pre/stop-nginx.sh <<EOF
#!/bin/sh
cd $PROJECT && $COMPOSE stop nginx
EOF
cat > /etc/letsencrypt/renewal-hooks/post/start-nginx.sh <<EOF
#!/bin/sh
cd $PROJECT && $COMPOSE start nginx
EOF
chmod +x /etc/letsencrypt/renewal-hooks/pre/stop-nginx.sh /etc/letsencrypt/renewal-hooks/post/start-nginx.sh
certbot renew --dry-run
```

## Оновлення коду

```bash
cd /var/www/gestia
git pull origin main
bash deploy/docker/deploy.sh
```

`git pull` без `--build` не оновлює image. Не патчити compose/nginx на сервері.

## Бекап

```bash
bash deploy/docker/backup-db.sh
```

Crontab: `0 3 * * * /var/www/gestia/deploy/docker/backup-db.sh`

## Резерв залишку

Карткове замовлення тримає склад, доки LiqPay не підтвердить оплату або не мине 24 години. Сторінки кошика, товару й оформлення доганяють прострочений резерв лише коли на них є трафік. Раз на годину з хоста:

```bash
cd /var/www/gestia && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T backend python manage.py release_expired_holds
```

Crontab: `15 * * * * cd /var/www/gestia && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T backend python manage.py release_expired_holds`

SMTP для `ORDER_NOTIFY_EMAIL` — лише якщо задано `EMAIL_HOST`.
