from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def memory_limit(value):
    """Removes all values of arg from the given string"""
    if not value:
        return ""
    if value < 80000:
        return f"{value} KB"
    else:
        return f"{value // 1024} MB"


@register.filter()
def time_limit(value):
    if not value:
        return ""

    if value < 1000:
        return f"{value} ms"
    else:
        return f"{(value / 1000.):.2f} seconds"


@register.filter(needs_autoescape=True)
def filename(value, autoescape=True):
    esc = conditional_escape if autoescape else lambda x: x
    if not value:
        return ""
    return mark_safe(f"<code>{esc(value)}</code>")
