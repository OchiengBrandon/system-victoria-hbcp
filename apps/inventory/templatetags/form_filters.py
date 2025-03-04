from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Adds a CSS class to a form field."""
    if hasattr(field, 'widget'):
        # Check if it's a BoundField
        existing_classes = field.widget.attrs.get('class', '')
        new_classes = ' '.join(filter(bool, [existing_classes, css_class]))
        field.widget.attrs['class'] = new_classes
        return field
    return field

@register.filter
def mul(value, arg):
    """Multiply value by arg."""
    return value * arg

@register.filter
def div(value, arg):
    """Divide value by arg."""
    return value / arg

@register.filter
def add(value, arg):
    """Add value and arg."""
    return value + arg