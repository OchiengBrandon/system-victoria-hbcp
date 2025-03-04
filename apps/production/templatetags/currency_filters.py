from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def to_kes(value):
    """Format value as KES currency."""
    try:
        # Convert value to Decimal for formatting
        value = Decimal(value)
        return f"KES {value:,.2f}" if value is not None else "KES 0.00"
    except (ValueError, TypeError, InvalidOperation):
        return "KES 0.00"  # Handle conversion errors