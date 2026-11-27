import json
import secrets

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from src.catalog.models import Product
from src.catalog.storefront import storefront_url
from src.commerce.cart import add, clear, lines, set_qty, signature
from src.commerce.cart_panel import cart_body_context, currency_of, render_panel
from src.commerce import payments
from src.commerce import wishlist as wish
from src.commerce.forms import (
    BuyNowForm,
    CallbackForm,
    CheckoutForm,
    ContactForm,
    style_form,
)
from src.commerce.models import Inquiry, Order
from src.commerce import novaposhta
from src.commerce import np_catalog
from src.commerce.services import (
    OrderValidationError,
    create_inquiry,
    create_order,
    insufficient_stock_message,
    normalize_idempotency_key,
    row_from_product,
    unavailable_message,
)
from src.commerce.stock_hold import release_expired_holds
from src.content.form_labels import label_form
from src.core.i18n import safe_next
from src.core.ratelimit import honeypot_filled, is_rate_limited, reject_if_limited
from src.core.utils import format_money


_NP_QUERY_MAX = 80
_NP_REF_MAX = 64
_CART_FLASH = "cart_flash"


def _currency(request):
    return currency_of(request)


def _np_blocked(request):
    if is_rate_limited(request, "np"):
        return JsonResponse({"items": []}, status=429)
    query = (request.GET.get("q") or "").strip()
    city_ref = (request.GET.get("city_ref") or "").strip()
    if len(query) > _NP_QUERY_MAX or len(city_ref) > _NP_REF_MAX:
        return JsonResponse({"items": []}, status=400)
    return None


def _hx(request):
    return request.headers.get("HX-Request")


def _panel(request):
    return request.POST.get("panel") == "1"


def _panel_sku(request, fallback=""):
    return (request.POST.get("panel_sku") or fallback or "").strip()


def _pretend_order_thanks(request):
    target = f"{reverse('thanks')}?kind=order"
    if _hx(request):
        response = HttpResponse()
        response["HX-Redirect"] = target
        return response
    return HttpResponseRedirect(target)


def _no_stock(product):
    return product.stock_status == Product.Stock.OUT or product.stock_qty <= 0


def _cart_notice(request, rows=None):
    parts = []
    if int(getattr(request, "_cart_removed", 0) or 0) > 0:
        parts.append(_("Деякі товари стали недоступні й прибрані з кошика."))
    for row in rows or []:
        if not row.get("over_stock"):
            continue
        parts.append(insufficient_stock_message(row["product"].name, row["product"].stock_qty))
    return " ".join(parts)


def _remember_order(request, number):
    raw = request.session.get("orders_done")
    done = [item for item in raw if isinstance(item, str)] if isinstance(raw, list) else []
    if number and number not in done:
        done.append(number)
    request.session["orders_done"] = done[-10:]


def _order_by_idem(raw):
    key = normalize_idempotency_key(raw)
    if not key:
        return None
    return Order.objects.filter(idempotency_key=key).first()


def _finish_checkout(request, order):
    clear(request)
    _remember_order(request, order.number)
    if (
        order.payment_method == Order.Payment.CARD
        and order.payment_status != Order.PayStatus.PAID
        and payments.card_enabled(order.currency)
    ):
        return HttpResponseRedirect(reverse("order_pay", kwargs={"number": order.number}))
    return HttpResponseRedirect(f"{reverse('thanks')}?kind=order&number={order.number}")


def _finish_buy_now(request, order):
    _remember_order(request, order.number)
    target = f"{reverse('thanks')}?kind=order&number={order.number}"
    if _hx(request):
        response = HttpResponse()
        response["HX-Redirect"] = target
        return response
    return HttpResponseRedirect(target)


def _customer(form):
    return {
        "name": form.cleaned_data["name"],
        "phone": form.cleaned_data["phone"],
        "email": form.cleaned_data["email"],
        "delivery_method": form.cleaned_data["delivery_method"],
        "address": form.cleaned_data["address"],
        "payment_method": form.cleaned_data["payment_method"],
        "np_city_ref": form.cleaned_data.get("city_ref") or "",
        "np_warehouse_ref": form.cleaned_data.get("warehouse_ref") or "",
    }


def _order_rows(rows):
    return [
        {
            "sku": row["sku"],
            "name": row["product"].name_uk,
            "qty": row["qty"],
            "unit": row["unit"],
            "line_total": row["line_total"],
        }
        for row in rows
    ]


def _checkout_post_ok(form, request, rows):
    ok = form.is_valid()
    for row in rows:
        if row.get("out_of_stock"):
            form.add_error(None, unavailable_message(row["product"].name))
            ok = False
        elif row.get("over_stock"):
            ok = False
    submitted = (request.POST.get("cart_sig") or "").strip()
    if submitted != signature(rows):
        form.add_error(
            None,
            _("Кошик або ціни змінилися. Перевірте суму та підтвердіть замовлення ще раз."),
        )
        ok = False
    return ok


def _fit_cart_to_stock(request, rows):
    notices = []
    changed = False
    for row in rows:
        product = row["product"]
        if row.get("out_of_stock") or product.stock_qty <= 0:
            set_qty(request, row["sku"], 0, stock_qty=0)
            notices.append(unavailable_message(product.name))
            changed = True
        elif row.get("over_stock"):
            set_qty(request, row["sku"], product.stock_qty, stock_qty=product.stock_qty)
            notices.append(insufficient_stock_message(product.name, product.stock_qty))
            changed = True
    return changed, " ".join(notices)


def _stash_cart_flash(request, notice):
    if notice:
        request.session[_CART_FLASH] = notice


def _take_cart_flash(request):
    notice = request.session.pop(_CART_FLASH, "")
    if notice:
        request.session.modified = True
    return notice if isinstance(notice, str) else ""


def _joined_notice(*parts):
    return " ".join(part for part in parts if part)


def _checkout_render(request, form, rows, total, currency, notice=""):
    return {
        "form": form,
        "rows": rows,
        "total": total,
        "total_label": format_money(total, currency),
        "cart_notice": _joined_notice(notice, _cart_notice(request, rows)),
        "cart_sig": signature(rows),
        "idem": secrets.token_urlsafe(16),
    }


@never_cache
def cart_page(request):
    release_expired_holds()
    currency = _currency(request)
    rows, total = lines(request, currency)
    notice = _joined_notice(_take_cart_flash(request), _cart_notice(request, rows))
    ctx = cart_body_context(request, rows, total, notice=notice)
    if _hx(request):
        return render(request, "commerce/_cart_body.html", ctx)
    return render(request, "commerce/cart.html", ctx)


def checkout(request):
    release_expired_holds()
    currency = _currency(request)
    card_ok = payments.card_enabled(currency)
    if request.method == "POST" and honeypot_filled(request):
        return _pretend_order_thanks(request)
    if request.method == "POST":
        existing = _order_by_idem(request.POST.get("idem"))
        if existing is not None:
            return _finish_checkout(request, existing)
    rows, total = lines(request, currency)
    changed, fit_notice = _fit_cart_to_stock(request, rows)
    if changed:
        rows, total = lines(request, currency)
    if not rows:
        _stash_cart_flash(request, fit_notice)
        return HttpResponseRedirect(reverse("cart"))
    form = style_form(CheckoutForm(request.POST or None, card_enabled=card_ok))
    if request.method == "POST" and reject_if_limited(request, form, "checkout"):
        return render(
            request,
            "commerce/checkout.html",
            _checkout_render(request, form, rows, total, currency, notice=fit_notice),
            status=429,
        )
    if request.method == "POST" and changed:
        return render(
            request,
            "commerce/checkout.html",
            _checkout_render(request, form, rows, total, currency, notice=fit_notice),
        )
    if request.method == "POST" and _checkout_post_ok(form, request, rows):
        try:
            order = create_order(
                source=Order.Source.CART,
                customer=_customer(form),
                rows=_order_rows(rows),
                currency=currency,
                language=request.LANGUAGE_CODE,
                idempotency_key=normalize_idempotency_key(request.POST.get("idem")),
            )
        except OrderValidationError as exc:
            form.add_error(None, exc.message)
        else:
            return _finish_checkout(request, order)
    return render(
        request,
        "commerce/checkout.html",
        _checkout_render(request, form, rows, total, currency, notice=fit_notice),
    )


@require_GET
def np_cities(request):
    blocked = _np_blocked(request)
    if blocked is not None:
        return blocked
    query = (request.GET.get("q") or "").strip()
    if len(query) < 2:
        return JsonResponse({"items": []})
    if np_catalog.has_cities():
        items = np_catalog.search_cities(query, limit=12)
    else:
        items = novaposhta.search_cities(query, limit=12)
    return JsonResponse({"items": items})


@require_GET
def np_warehouses(request):
    blocked = _np_blocked(request)
    if blocked is not None:
        return blocked
    query = (request.GET.get("q") or "").strip()
    city_ref = (request.GET.get("city_ref") or "").strip()
    kind = "locker" if request.GET.get("kind") == "locker" else "branch"
    if len(query) < 2:
        return JsonResponse({"items": []})
    items = np_catalog.search_warehouses(query, city_ref=city_ref, kind=kind, limit=30)
    return JsonResponse({"items": items})


@require_GET
def np_streets(request):
    blocked = _np_blocked(request)
    if blocked is not None:
        return blocked
    city_ref = (request.GET.get("city_ref") or "").strip()
    query = (request.GET.get("q") or "").strip()
    if len(query) < 2 or not city_ref:
        return JsonResponse({"items": []})
    if not novaposhta.configured() and not novaposhta.demo_mode():
        return JsonResponse({"items": [], "error": "not_configured"}, status=503)
    return JsonResponse({"items": novaposhta.search_streets(city_ref, query, limit=20)})


@csrf_exempt
@never_cache
def thanks(request):
    # LiqPay may POST the buyer to result_url; ignore body and bounce to GET.
    if request.method == "POST":
        response = HttpResponseRedirect(request.get_full_path())
        response.status_code = 303
        return response

    from src.content.models_thankyou import ThankYouPage

    kind = request.GET.get("kind", "order")
    number = (request.GET.get("number") or "").strip()
    done = request.session.get("orders_done")
    if not isinstance(done, list) or number not in done:
        number = ""
    order = None
    pay_retry_url = ""
    if number:
        order = Order.objects.filter(number=number).first()
        if (
            order is not None
            and order.payment_method == Order.Payment.CARD
            and order.payment_status == Order.PayStatus.FAILED
            and payments.card_enabled(order.currency)
        ):
            pay_retry_url = reverse("order_pay", kwargs={"number": order.number})
    return render(
        request,
        "commerce/thanks.html",
        {
            "kind": kind,
            "number": number,
            "order": order,
            "pay_retry_url": pay_retry_url,
            "thanks_page": ThankYouPage.load(),
        },
    )


@never_cache
@require_GET
def order_pay(request, number):
    # Session-gated retry. Failed with stock → new payment_ref. Without stock → no LiqPay form.
    done = request.session.get("orders_done")
    if not isinstance(done, list) or number not in done:
        return HttpResponseRedirect(f"{reverse('thanks')}?kind=order")
    order = get_object_or_404(Order, number=number)
    if order.payment_method != Order.Payment.CARD or order.payment_status == Order.PayStatus.PAID:
        return HttpResponseRedirect(f"{reverse('thanks')}?kind=order&number={order.number}")
    if not payments.card_enabled(order.currency):
        return HttpResponseRedirect(f"{reverse('thanks')}?kind=order&number={order.number}")
    payload = payments.build_checkout(order, request)
    if order.payment_status == Order.PayStatus.PAID:
        return HttpResponseRedirect(f"{reverse('thanks')}?kind=order&number={order.number}")
    blocked = bool(payload.get("stock_blocked"))
    return render(
        request,
        "commerce/pay.html",
        {
            "order": order,
            "checkout_url": payload["checkout_url"],
            "data": payload["data"],
            "signature": payload["signature"],
            "pay_blocked": blocked,
            "pay_error": (
                _("Цього товару вже немає в наявності, тож оплатити замовлення не вийде.")
                if blocked
                else ""
            ),
        },
    )


@csrf_exempt
@never_cache
@require_POST
def liqpay_callback(request):
    # Signature verified inside handle_callback before any order mutation.
    status, body = payments.handle_callback(
        request.POST.get("data", ""),
        request.POST.get("signature", ""),
    )
    return HttpResponse(body, status=status)


def wishlist_page(request):
    currency = _currency(request)
    items = wish.products(request)
    rows = [
        {
            "product": product,
            "sku": product.sku,
            "unit": product.amount(currency),
            "unit_label": format_money(product.amount(currency), currency),
            "in_wishlist": True,
        }
        for product in items
    ]
    return render(
        request,
        "commerce/wishlist.html",
        {"rows": rows, "wishlist_count": len(rows)},
    )


@never_cache
@require_POST
def wishlist_toggle(request):
    if is_rate_limited(request, "wishlist"):
        return HttpResponse(status=429)
    product = get_object_or_404(Product, sku=request.POST.get("sku", ""), is_active=True)
    active = wish.toggle(request, product.sku)
    variant = request.POST.get("variant") or ""
    if variant != "nd":
        variant = ""
    if _hx(request):
        return render(
            request,
            "partials/wishlist_toggle_response.html",
            {
                "product": product,
                "in_wishlist": active,
                "variant": variant,
                "wishlist_count": wish.item_count(request),
            },
        )
    next_url = safe_next(request.POST.get("next") or storefront_url(product))
    return HttpResponseRedirect(next_url)


@never_cache
@require_POST
def wishlist_remove(request):
    if is_rate_limited(request, "wishlist"):
        return HttpResponse(status=429)
    sku = request.POST.get("sku", "")
    wish.remove(request, sku)
    if _hx(request):
        currency = _currency(request)
        items = wish.products(request)
        rows = [
            {
                "product": product,
                "sku": product.sku,
                "unit": product.amount(currency),
                "unit_label": format_money(product.amount(currency), currency),
                "in_wishlist": True,
            }
            for product in items
        ]
        return render(
            request,
            "commerce/_wishlist_body.html",
            {"rows": rows, "wishlist_count": len(rows)},
        )
    return HttpResponseRedirect(reverse("wishlist"))


@never_cache
@require_POST
def cart_add(request):
    release_expired_holds()
    if is_rate_limited(request, "cart"):
        return HttpResponse(status=429)
    product = get_object_or_404(Product, sku=request.POST.get("sku", ""), is_active=True)
    if _no_stock(product):
        return HttpResponse(status=422)
    try:
        qty = int(request.POST.get("qty", "1"))
    except (TypeError, ValueError):
        qty = 1
    add(request, product.sku, qty, stock_qty=product.stock_qty)
    if _hx(request) and _panel(request):
        response = render_panel(request, _panel_sku(request, product.sku))
        response["HX-Trigger"] = json.dumps({"nd:cart-changed": True})
        return response
    if _hx(request):
        response = render(
            request,
            "partials/cart_count_response.html",
            {"cart_count": sum_count(request)},
        )
        response["HX-Trigger"] = json.dumps({"nd:cart-added": {"sku": product.sku}})
        return response
    return HttpResponseRedirect(storefront_url(product))


def sum_count(request):
    from src.commerce.cart import item_count

    return item_count(request)


@never_cache
@require_GET
def cart_panel(request):
    sku = (request.GET.get("sku") or "").strip()
    return render_panel(request, sku)


@never_cache
@require_POST
def cart_update(request):
    release_expired_holds()
    if is_rate_limited(request, "cart"):
        return HttpResponse(status=429)
    sku = request.POST.get("sku", "")
    try:
        qty = int(request.POST.get("qty", "1"))
    except (TypeError, ValueError):
        qty = 1
    product = Product.objects.filter(sku=sku, is_active=True).first()
    if qty > 0 and product is not None and _no_stock(product):
        return HttpResponse(status=422)
    stock_qty = product.stock_qty if product is not None else None
    set_qty(request, sku, qty, stock_qty=stock_qty)
    if _hx(request) and _panel(request):
        response = render_panel(request, _panel_sku(request, sku))
        response["HX-Trigger"] = json.dumps({"nd:cart-changed": True})
        return response
    if _hx(request):
        currency = _currency(request)
        rows, total = lines(request, currency)
        return render(
            request,
            "commerce/_cart_body.html",
            cart_body_context(request, rows, total, notice=_cart_notice(request, rows)),
        )
    return HttpResponseRedirect(reverse("cart"))


@require_POST
def callback(request):
    if honeypot_filled(request):
        return render(request, "commerce/_thanks_lead.html", {"long": True})
    form = label_form(style_form(CallbackForm(request.POST)))
    if reject_if_limited(request, form, "callback"):
        return render(request, "commerce/_callback_form.html", {"callback_form": form}, status=429)
    if not form.is_valid():
        status = 422 if _hx(request) else 200
        return render(request, "commerce/_callback_form.html", {"callback_form": form}, status=status)
    create_inquiry(
        kind=Inquiry.Kind.CALLBACK,
        name=form.cleaned_data["name"],
        phone=form.cleaned_data["phone"],
        sku=form.cleaned_data["sku"],
        consent=True,
    )
    return render(request, "commerce/_thanks_lead.html", {"long": True})


@require_POST
def buy_now(request):
    release_expired_holds()
    if honeypot_filled(request):
        return _pretend_order_thanks(request)
    existing = _order_by_idem(request.POST.get("idem"))
    if existing is not None:
        return _finish_buy_now(request, existing)
    form = label_form(style_form(BuyNowForm(request.POST)))
    if reject_if_limited(request, form, "buy_now"):
        return render(request, "commerce/_buy_form.html", {"buy_form": form}, status=429)
    product = Product.objects.filter(sku=request.POST.get("sku", ""), is_active=True).first()
    valid = form.is_valid()
    if product is None or product.stock_status == Product.Stock.OUT:
        form.add_error(None, _("Цей товар зараз не можна замовити."))
        valid = False
    if valid and product is not None:
        currency = _currency(request)
        try:
            order = create_order(
                source=Order.Source.BUY_NOW,
                customer={
                    "name": form.cleaned_data["name"],
                    "phone": form.cleaned_data["phone"],
                    "email": "",
                    "delivery_method": Order.Delivery.COURIER,
                    "address": form.cleaned_data["address"],
                    "payment_method": Order.Payment.ON_DELIVERY,
                },
                rows=[row_from_product(product, 1, currency)],
                currency=currency,
                language=request.LANGUAGE_CODE,
                idempotency_key=normalize_idempotency_key(request.POST.get("idem")),
            )
        except OrderValidationError as exc:
            form.add_error(None, exc.message)
        else:
            return _finish_buy_now(request, order)
    status = 422 if _hx(request) else 200
    return render(request, "commerce/_buy_form.html", {"buy_form": form}, status=status)


@require_POST
def contact(request):
    if honeypot_filled(request):
        return render(request, "commerce/_thanks_lead.html", {"long": False})
    form = label_form(style_form(ContactForm(request.POST)))
    if reject_if_limited(request, form, "contact"):
        return render(request, "commerce/_contact_form.html", {"contact_form": form}, status=429)
    if not form.is_valid():
        status = 422 if _hx(request) else 200
        return render(request, "commerce/_contact_form.html", {"contact_form": form}, status=status)
    create_inquiry(
        kind=Inquiry.Kind.CONTACT,
        name=form.cleaned_data["name"],
        phone=form.cleaned_data["phone"],
        message=form.cleaned_data["message"],
        consent=True,
    )
    return render(request, "commerce/_thanks_lead.html", {"long": False})
