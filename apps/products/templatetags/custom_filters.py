from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()

@register.filter
def divide(value, arg):
    """Divide two values."""
    try:
        return Decimal(value) / Decimal(arg)
    except (ZeroDivisionError, ValueError, TypeError, InvalidOperation):
        return 0  # Handle errors appropriately