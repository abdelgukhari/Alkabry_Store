from django import template

register = template.Library()


@register.filter(name='replace')
def replace(value, args):
    """Replace occurrences of a string with another string."""
    old, new = args.split(',')
    return value.replace(old.strip(), new.strip())


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Get item from dictionary by key. Usage: {{ dict|get_item:key }}"""
    return dictionary.get(key)
