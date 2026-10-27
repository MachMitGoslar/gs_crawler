"""Date handling for the generic scraper (publication dates from web pages)."""

import re
from datetime import datetime, timedelta
from typing import Optional


PUBLISHED_AT_FORMAT = '%Y-%m-%dT%H:%M'

GERMAN_MONTHS = {
    'januar': 1, 'jan': 1, 'februar': 2, 'feb': 2, 'märz': 3, 'maerz': 3, 'mär': 3,
    'april': 4, 'apr': 4, 'mai': 5, 'juni': 6, 'jun': 6, 'juli': 7, 'jul': 7,
    'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9, 'oktober': 10, 'okt': 10,
    'november': 11, 'nov': 11, 'dezember': 12, 'dez': 12,
}


def _german_month_to_number(value: str, date_format: str):
    """Replace a German month name in value by its number (and %B/%b in the format by %m).

    strptime's %B/%b depend on the process locale, which is C in the container, so German
    names would never match there.
    """
    def replace(match):
        number = GERMAN_MONTHS.get(match.group(0).lower().rstrip('.'))
        return str(number) if number else match.group(0)

    value = re.sub(r'[A-Za-zäöüÄÖÜ]+\.?', replace, value, count=1)
    return value, date_format.replace('%B', '%m').replace('%b', '%m')


def parse_published_at(value: Optional[str], date_format: Optional[str] = None) -> Optional[str]:
    """Normalize a date from the page to PUBLISHED_AT_FORMAT, or None if it cannot be parsed.

    date_format is a strptime pattern (e.g. '%d.%m.%Y'); without it ISO 8601 is expected
    ('2026-10-25', '2026-10-25T10:00:00+01:00', '...Z'). German month names work with
    %B/%b regardless of the locale ('23. Oktober' with '%d. %B'). If the format has no year
    the current year is used, or the previous one if that would put the date in the future
    (a December date seen in January). Time zones are dropped, the wall-clock time is kept.
    """
    if not value:
        return None
    value = value.strip()
    try:
        if date_format:
            if '%B' in date_format or '%b' in date_format:
                value, date_format = _german_month_to_number(value, date_format)
            has_year = '%Y' in date_format or '%y' in date_format
            if not has_year:
                now = datetime.now()
                value, date_format = f"{value} {now.year}", f"{date_format} %Y"
            parsed = datetime.strptime(value, date_format)
            if not has_year and parsed > now + timedelta(days=1):
                parsed = parsed.replace(year=parsed.year - 1)
        else:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    return parsed.strftime(PUBLISHED_AT_FORMAT)
