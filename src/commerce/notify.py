import html
import logging

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("src.commerce")
REQUEST_TIMEOUT = 5


def send_telegram_message(text: str) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        logger.info("Telegram не налаштований — повідомлення лише в лог")
        return False
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Не вдалося надіслати Telegram-сповіщення")
        return False


def _esc(value) -> str:
    return html.escape(str(value or ""))


def _mail_lang(order) -> str:
    from src.content.models_thankyou import EMAIL_SUBJECT_DEFAULTS

    lang = str(getattr(order, "language", "") or "uk").split("-")[0]
    if lang not in EMAIL_SUBJECT_DEFAULTS:
        return "uk"
    return lang


def _with_number(template: str, number) -> str:
    return str(template or "").replace("{number}", "" if number is None else str(number))


def customer_order_mail(order):
    from src.content.models_thankyou import (
        EMAIL_BODY_DEFAULTS,
        EMAIL_SUBJECT_DEFAULTS,
        ThankYouPage,
    )
    from src.core.utils import localized

    lang = _mail_lang(order)
    page = ThankYouPage.load()
    subject = (localized(page, "email_subject", lang) or "").strip()
    body = (localized(page, "email_body", lang) or "").strip()
    if not subject:
        subject = EMAIL_SUBJECT_DEFAULTS[lang]
    if not body:
        body = EMAIL_BODY_DEFAULTS[lang]
    number = order.number
    return _with_number(subject, number), _with_number(body, number)


def notify_order(order_id: int):
    from src.commerce.models import Order

    try:
        order = Order.objects.prefetch_related("items").get(pk=order_id)
    except Order.DoesNotExist:
        return
    lines = [
        f"<b>Замовлення {_esc(order.number)}</b>",
        _esc(order.get_source_display()),
        f"{_esc(order.customer_name)} · {_esc(order.phone)}",
    ]
    if order.email:
        lines.append(_esc(order.email))
    for item in order.items.all():
        lines.append(f"{_esc(item.name)} ({_esc(item.sku)}) × {item.qty}")
    lines.append(f"{order.total} {order.currency}")
    lines.append(_esc(order.get_delivery_method_display()))
    lines.append(_esc(order.delivery_address))
    lines.append(_esc(order.get_payment_status_display()))
    send_telegram_message("\n".join(lines))
    if settings.ORDER_NOTIFY_EMAIL:
        send_mail(
            subject=f"Замовлення {order.number}",
            message="\n".join(
                [
                    order.number,
                    order.customer_name,
                    order.phone,
                    order.email,
                    order.delivery_address,
                    str(order.total),
                ]
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ORDER_NOTIFY_EMAIL],
            fail_silently=True,
        )
    if order.email:
        subject, message = customer_order_mail(order)
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=True,
        )


def notify_inquiry(inquiry_id: int):
    from src.commerce.models import Inquiry

    try:
        inquiry = Inquiry.objects.get(pk=inquiry_id)
    except Inquiry.DoesNotExist:
        return
    lines = [
        f"<b>{_esc(inquiry.get_kind_display())}</b>",
    ]
    if inquiry.name or inquiry.phone:
        lines.append(f"{_esc(inquiry.name)} · {_esc(inquiry.phone)}")
    if inquiry.email:
        lines.append(_esc(inquiry.email))
    if inquiry.product_name:
        lines.append(f"{_esc(inquiry.product_name)} · {_esc(inquiry.sku)}")
    if inquiry.message:
        lines.append(_esc(inquiry.message))
    send_telegram_message("\n".join(lines))
    if settings.ORDER_NOTIFY_EMAIL:
        send_mail(
            subject=inquiry.get_kind_display(),
            message="\n".join(
                [
                    inquiry.get_kind_display(),
                    inquiry.name,
                    inquiry.phone,
                    inquiry.email,
                    inquiry.product_name,
                    inquiry.sku,
                    inquiry.message,
                ]
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ORDER_NOTIFY_EMAIL],
            fail_silently=True,
        )
