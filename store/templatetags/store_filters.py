from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return Decimal('0.00')

@register.filter(name='subtract')
def subtract(value, arg):
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return Decimal('0.00')

@register.filter(name='addclass')
def addclass(field, css_class):
    return field.as_widget(attrs={'class': css_class})
