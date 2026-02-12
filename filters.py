# filters.py
from datetime import datetime
from flask import Blueprint

filters_bp = Blueprint('filters', __name__)

@filters_bp.app_template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    """Format a datetime object or ISO string."""
    if not value:
        return ''
    
    if isinstance(value, str):
        try:
            # Try to parse ISO format
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return value
    
    if isinstance(value, datetime):
        return value.strftime(format)
    
    return str(value)

@filters_bp.app_template_filter('shortdate')
def shortdate(value):
    """Format date in short format."""
    return datetimeformat(value, '%Y-%m-%d')

@filters_bp.app_template_filter('timeago')
def timeago(value):
    """Format time as "time ago"."""
    if not value:
        return ''
    
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return value
    
    if not isinstance(value, datetime):
        return str(value)
    
    now = datetime.now()
    diff = now - value
    
    if diff.days > 365:
        years = diff.days // 365
        return f'{years} year{"s" if years > 1 else ""} ago'
    elif diff.days > 30:
        months = diff.days // 30
        return f'{months} month{"s" if months > 1 else ""} ago'
    elif diff.days > 0:
        return f'{diff.days} day{"s" if diff.days > 1 else ""} ago'
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
    else:
        return 'just now'