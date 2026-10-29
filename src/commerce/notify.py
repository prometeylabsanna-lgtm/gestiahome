import html
import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils import translation
from django.utils.translation import gettext as _

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
        with translation.override(order.language or "uk"):
            send_mail(
                subject=_("Замовлення %(number)s") % {"number": order.number},
                message=_(
                    "Дякуємо за замовлення, найближчим часом наш консультант зв'яжеться з вами. Номер: %(number)s"
                )
                % {"number": order.number},
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
