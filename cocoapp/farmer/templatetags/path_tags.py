from django import template

register = template.Library()

@register.filter
def starts_with(value, arg):
    """Returns True if the value starts with the argument."""
    return value.startswith(arg)