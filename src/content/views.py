from types import SimpleNamespace

from django.db.utils import OperationalError, ProgrammingError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from src.commerce.forms import ContactForm, style_form
from src.commerce.models import Inquiry
from src.commerce.services import create_inquiry
from src.commerce.wishlist import sku_set
from src.content.home_slots import home_popular
from src.content.legal_pages import legal_document
from src.content.models import AboutPage, HomeBlock, HomeCollection
from src.content.models_faq import FaqPage
from src.catalog.menu_filters import catalog_href, group_key
from src.content.models_menu import MenuGroupItem
from src.core.ratelimit import honeypot_filled, reject_if_limited


def _home_collections():
    try:
        rows = list(
            HomeCollection.objects.filter(is_active=True, block__key=HomeBlock.Key.COLLECTIONS)
            .select_related("category")
            .order_by("sort", "id")
        )
        if rows:
            return rows
        return list(
            HomeCollection.objects.filter(is_active=True, block__isnull=True)
            .select_related("category")
            .order_by("sort", "id")
        )
    except (OperationalError, ProgrammingError):
        return []


@require_http_methods(["GET", "HEAD", "POST"])
def home(request):
    if request.method == "POST" and honeypot_filled(request):
        return redirect(f"{reverse('thanks')}?kind=contact")
    form = style_form(ContactForm(request.POST or None))
    status = 200
    if request.method == "POST" and reject_if_limited(request, form, "home"):
        status = 429
    elif request.method == "POST" and form.is_valid():
        create_inquiry(
            kind=Inquiry.Kind.CONTACT,
            name=form.cleaned_data["name"],
            phone=form.cleaned_data["phone"],
            message=form.cleaned_data["message"],
            consent=True,
        )
        return redirect(f"{reverse('thanks')}?kind=contact")
    return render(
        request,
        "content/home.html",
        {
            "popular": home_popular(),
            "collections": _home_collections(),
            "wishlist_skus": sku_set(request),
            "home_form": form,
        },
        status=status,
    )


def _figma_block(key, title, cta=""):
    block = HomeBlock.objects.filter(key=key).first()
    if block is not None:
        return block
    return SimpleNamespace(title=title, cta=cta)


def about(request):
    page = AboutPage.load()
    return render(request, "content/about.html", {"page": page})


def faq(request):
    page = FaqPage.load()
    items = page.items.filter(is_active=True)
    return render(
        request,
        "content/faq.html",
        {
            "page": page,
            "items": items,
        },
    )


def _collection_addons(collection):
    """Порядок додатків такий, як у макеті, а не алфавіт товарів."""
    through = collection.addons.through
    ordered_ids = list(
        through.objects.filter(homecollection_id=collection.pk)
        .order_by("id")
        .values_list("product_id", flat=True)
    )
    products = {
        product.pk: product
        for product in collection.addons.filter(is_active=True, pk__in=ordered_ids)
    }
    return [products[pk] for pk in ordered_ids if pk in products]


def collection_detail(request, slug):
    collection = get_object_or_404(
        HomeCollection.objects.select_related("product", "category").prefetch_related(
            "gallery_images",
            "addons",
        ),
        slug=slug,
        is_active=True,
    )
    blocks = {
        block.key: block
        for block in HomeBlock.objects.filter(key__in=["pdp_ship", "pdp_pay"])
    }
    others = (
        HomeCollection.objects.filter(is_active=True)
        .exclude(pk=collection.pk)
        .exclude(slug="")
        .exclude(slug__isnull=True)
        .select_related("category")
        .order_by("sort", "id")
    )
    menu_item = (
        MenuGroupItem.objects.filter(
            collection_id=collection.pk,
            is_active=True,
            group__is_active=True,
        )
        .select_related("group")
        .order_by("group__sort", "sort", "id")
        .first()
    )
    return render(
        request,
        "content/collection.html",
        {
            "collection": collection,
            "gallery": collection.gallery_photos(),
            "addons": _collection_addons(collection),
            "others": others,
            "ship_block": blocks.get("pdp_ship"),
            "pay_block": blocks.get("pdp_pay"),
            "menu_group": menu_item.group if menu_item else None,
            "crumb_group_url": catalog_href(group_key(menu_item.group)) if menu_item else "",
            "crumb_current": menu_item.label if menu_item else collection.title,
        },
    )


def legal_page(request, slug):
    doc = legal_document(slug)
    if doc is None:
        raise Http404
    return render(request, "content/legal.html", {"doc": doc})


def privacy(request):
    return legal_page(request, "privacy")


def offer(request):
    return legal_page(request, "offer")


def cookies(request):
    return legal_page(request, "cookies")


def shipping(request):
    return legal_page(request, "shipping")


def _tel_href(phone: str) -> str:
    kept = []
    for char in phone:
        if char.isdigit() or (char == "+" and not kept):
            kept.append(char)
    return "tel:" + "".join(kept)


def _contacts_nap():
    from src.content.models import SiteSettings
    from src.core.utils import localized

    site = SiteSettings.load()
    socials = []
    for label, attr in (
        ("Instagram", "instagram_url"),
        ("Pinterest", "pinterest_url"),
        ("Telegram", "telegram_url"),
    ):
        href = " ".join(str(getattr(site, attr, "") or "").split())
        if href:
            socials.append({"label": label, "href": href})
    phone = " ".join(str(site.phone or "").split()) or "+380 00 000 00 00"
    return {
        "phone": phone,
        "phone_href": _tel_href(phone),
        "email": " ".join(str(site.email or "").split()),
        "address": " ".join(str(localized(site, "address") or "").split()),
        "socials": socials,
    }


def _contacts_form_context(request, form):
    from src.content.models_contacts import ContactsPage

    page = ContactsPage.load()
    return {
        "contact_form": form,
        "contacts_page": page,
        "submit_label": page.form_title,
        "form_action": request.path,
    }


def _contacts_thanks(request):
    if request.headers.get("HX-Request"):
        return render(request, "commerce/_thanks_lead.html", {"long": False})
    return redirect(f"{reverse('thanks')}?kind=contact")


@require_http_methods(["GET", "HEAD", "POST"])
def contacts(request):
    from src.content.form_labels import label_form

    bound = request.method == "POST"
    form = label_form(style_form(ContactForm(request.POST if bound else None)))
    status = 200
    if bound:
        if honeypot_filled(request):
            return _contacts_thanks(request)
        if reject_if_limited(request, form, "contact"):
            status = 429
        elif form.is_valid():
            create_inquiry(
                kind=Inquiry.Kind.CONTACT,
                name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"],
                message=form.cleaned_data["message"],
                consent=True,
            )
            return _contacts_thanks(request)
        elif request.headers.get("HX-Request"):
            status = 422
        if request.headers.get("HX-Request"):
            return render(
                request,
                "commerce/_contact_form.html",
                _contacts_form_context(request, form),
                status=status,
            )
    return render(
        request,
        "content/contacts.html",
        {"contact_form": form, "nap": _contacts_nap(), **_contacts_form_context(request, form)},
        status=status,
    )
