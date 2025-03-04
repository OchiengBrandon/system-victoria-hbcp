from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        # Ensure both values are converted to Decimal for multiplication
        return Decimal(value) * Decimal(arg)
    except (ValueError, TypeError, InvalidOperation):
        return 0  # or handle it as you prefer