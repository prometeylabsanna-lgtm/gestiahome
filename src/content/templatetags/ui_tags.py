from django import template

from src.content.ui_text import text

register = template.Library()


@register.simple_tag(takes_context=True)
def ui(context, key, **slots):
    del context
    return text(key, **slots)
