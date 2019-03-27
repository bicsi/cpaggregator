from django import template

register = template.Library()


@register.filter()
def has_account(user, judge):
    return user.profile.handles.filter(judge=judge).exists()