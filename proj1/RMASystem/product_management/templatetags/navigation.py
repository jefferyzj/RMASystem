from django import template

register = template.Library()

@register.inclusion_tag('navigation.html')
def navigation_menu():
    return {}
