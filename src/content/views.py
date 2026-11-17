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
from src.content.home_slots import home_categories, home_popular
from src.content.legal_pages import legal_document
from src.content.models import AboutPage, Advantage, HomeBlock, HomeCollection, Review
from src.content.models_faq import FaqPage
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
    advantages = Advantage.objects.filter(block__key=HomeBlock.Key.ADVANTAGES)
    if not advantages.exists():
        advantages = Advantage.objects.filter(block__isnull=True)
    return render(
        request,
        "content/home.html",
        {
            "categories": home_categories(),
            "popular": home_popular(),
            "collections": _home_collections(),
            "advantages": advantages,
            "reviews": Review.objects.filter(placement=Review.Placement.HOME),
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
            "addons": list(collection.addons.filter(is_active=True)),
            "others": others,
            "ship_block": blocks.get("pdp_ship"),
            "pay_block": blocks.get("pdp_pay"),
            "menu_group": menu_item.group if menu_item else None,
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
