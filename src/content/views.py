from types import SimpleNamespace

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from src.commerce.forms import ContactForm, style_form
from src.commerce.models import Inquiry
from src.commerce.services import create_inquiry
from src.core.ratelimit import honeypot_filled, reject_if_limited
from src.content.home_slots import about_popular, home_categories, home_popular
from src.content.legal_pages import legal_document
from src.content.models import AboutPage, Advantage, HomeBlock, Review


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
            "advantages": advantages,
            "reviews": Review.objects.filter(placement=Review.Placement.HOME),
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
    popular_title = page.popular_title or "Популярні товари"
    popular_cta = page.popular_cta or "Перейти до каталогу"
    reviews_title = page.reviews_title or "Відгуки"
    return render(
        request,
        "content/about.html",
        {
            "page": page,
            "popular": about_popular(),
            "reviews": Review.objects.filter(placement=Review.Placement.ABOUT),
            "popular_block": SimpleNamespace(title=popular_title, cta=popular_cta),
            "reviews_block": SimpleNamespace(title=reviews_title),
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
