from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply two values."""
    try:
        # Ensure both values are converted to Decimal for multiplication
        return Decimal(value) * Decimal(arg)
    except (ValueError, TypeError, InvalidOperation):
        return 0  # or handle it as you prefer

@register.filter(name='add_class')
def add_class(field, css_class):
    """Add a CSS class to a form field."""
    return field.as_widget(attrs={'class': css_class})

@register.filter
def divide(value, arg):
    """Divide two values."""
    try:
        # Ensure both values are converted to Decimal for division
        return Decimal(value) / Decimal(arg)
    except (ZeroDivisionError, ValueError, TypeError, InvalidOperation):
        return 0  # or handle it as you prefer