__author__ = 'Exlivris3'
import datetime
from django.utils.timezone import is_aware, utc
from django.utils.translation import ugettext, ungettext_lazy
from django.utils.html import avoid_wrapping

from django import template

register = template.Library()

def daysince(d, now=None, reversed=False):
    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime.datetime):
        d = datetime.datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime(now.year, now.month, now.day)

    if not now:
        now = datetime.datetime.now(utc if is_aware(d) else None)

    delta = (d - now) if reversed else (now - d)
    # ignore microseconds
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return "0"
    count = since // (60 * 60 * 24)
    return count


def daysuntil(d, now=None):
    """
    Like timesince, but returns a string measuring the time until
    the given time.
    """
    return daysince(d, now, reversed=True)


@register.filter("daysuntil", is_safe=False)
def daysuntil_filter(value, arg=None):
    """Formats a date as the time until that date (i.e. "4")."""
    if not value:
        return ''
    try:
        return daysuntil(value, arg)
    except (ValueError, TypeError):
        return ''

