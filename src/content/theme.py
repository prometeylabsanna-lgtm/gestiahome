import re

from django.db.utils import OperationalError, ProgrammingError

from src.content.colors import TOKEN_ACCENT, TOKEN_CHROME, TOKEN_INK, TOKEN_PAPER, normalize_hex
from src.content.models_styles import FONT_INTER, FONT_STACKS

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

URL_PAGE = {
    "home": "home",
    "catalog": "catalog",
    "category": "catalog",
    "product": "product",
    "cart": "cart",
    "checkout": "checkout",
    "about": "about",
    "privacy": "legal",
    "offer": "legal",
    "cookies": "legal",
    "shipping": "legal",
}


def page_style_key(request) -> str:
    match = getattr(request, "resolver_match", None)
    name = getattr(match, "url_name", "") if match else ""
    return URL_PAGE.get(name or "", "")


def _site_color(value: str | None, fallback: str) -> str:
    raw = value or ""
    if _HEX.match(raw):
        return raw
    return fallback


def global_style():
    from src.content.models_styles import PageStyle

    try:
        return PageStyle.objects.filter(page=PageStyle.Key.GLOBAL).first()
    except (OperationalError, ProgrammingError):
        return None


def theme_font_family() -> str:
    row = global_style()
    if row is None:
        return FONT_INTER
    return row.font_family or FONT_INTER


def theme_font_stack() -> str:
    return FONT_STACKS.get(theme_font_family(), FONT_STACKS[FONT_INTER])


def _chrome_fg(chrome: str) -> str:
    raw = (chrome or TOKEN_CHROME).lstrip("#")
    if len(raw) != 6:
        return TOKEN_INK
    try:
        r, g, b = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    except ValueError:
        return TOKEN_INK
    # Світлий фон хедера/футера — темний текст; темний — кремовий як у макеті.
    if (0.299 * r + 0.587 * g + 0.114 * b) > 160:
        return TOKEN_INK
    return "#feedda"


def build_theme_css() -> str:
    from src.content.models import SiteSettings

    site = SiteSettings.load()
    ink = _site_color(site.color_ink, TOKEN_INK)
    paper = _site_color(site.color_paper, TOKEN_PAPER)
    accent = _site_color(site.color_accent, TOKEN_ACCENT)
    row = global_style()
    chrome = TOKEN_CHROME
    font = FONT_STACKS[FONT_INTER]
    if row is not None:
        chrome = normalize_hex(row.chrome_background_color) or TOKEN_CHROME
        font = row.font_stack
        ink = normalize_hex(row.text_color) or ink
        paper = normalize_hex(row.background_color) or paper
        accent = normalize_hex(row.hover_color) or accent

    chrome_fg = _chrome_fg(chrome)
    root = (
        f":root{{--ink:{ink};--paper:{paper};--accent:{accent};"
        f"--chrome:{chrome};--chrome-fg:{chrome_fg};--font:{font};}}"
    )
    # Дефолтний білий = як у макеті: біла шапка, темний підвал із footer.css.
    # Будь-який інший chrome — спільний фон шапки і підвалу.
    chrome_rule = ".site-header,.site-header__bar{background:var(--chrome)}"
    if chrome.lower() != TOKEN_CHROME.lower():
        chrome_rule += (
            ".site-footer{background:var(--chrome);color:var(--chrome-fg)}"
            ".site-footer a,.site-footer__col a,.site-footer__legal,"
            ".site-footer__credit,.site-footer__lead,.site-footer__tail,"
            ".site-footer__credit-link,.site-footer__credit-name{color:var(--chrome-fg)}"
        )
    if accent.lower() == TOKEN_ACCENT.lower():
        hover = ""
    else:
        hover = (
            f":root{{--hover:{accent.lower()};}}"
            "body a:hover,body button:hover{color:var(--hover)}"
        )
    return root + hover + chrome_rule
