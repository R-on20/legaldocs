from django import template

register = template.Library()

@register.filter
def replace_underscore(value):
    """Replace underscores with spaces and capitalize"""
    if isinstance(value, str):
        return value.replace('_', ' ').title()
    return value

@register.filter
def format_field_name(value):
    """Format field names for display"""
    if isinstance(value, str):
        # Replace underscores with spaces, then title case
        formatted = value.replace('_', ' ').title()
        # Handle some special cases
        formatted = formatted.replace('Ip', 'IP')
        formatted = formatted.replace('Id', 'ID')
        formatted = formatted.replace('Url', 'URL')
        return formatted
    return value
