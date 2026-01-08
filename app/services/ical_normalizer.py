import re
import uuid
from datetime import timedelta
from typing import List, Optional, Dict, Any

from dateutil import parser as dateparser


class IcalNormalizer:
    """Helpers to normalize extracted values into iCalendar-friendly forms.

    Each helper returns a normalized value suitable for mapping into an iCal
    property (or None). Methods are small and focused so they can be used
    independently for each supported field.
    """

    DATE_ONLY_RE = re.compile(r"^\s*\d{4}-\d{2}-\d{2}\s*$")

    @staticmethod
    def normalize_text(value: Optional[str]) -> Optional[str]:
        """Escape TEXT per RFC5545 (comma, semicolon, backslash, newlines).

        Returns escaped string or None.
        """
        if value is None:
            return None
        s = value
        s = s.replace("\\", "\\\\")
        s = s.replace("\n", "\\n")
        s = s.replace(",", "\\,")
        s = s.replace(";", "\\;")
        return s

    @staticmethod
    def fold_line(line: str, width: int = 75) -> str:
        """Fold a long property line into RFC-compliant folded lines (CRLF + space).

        Note: returns a string using CRLF sequences.
        """
        if not line or len(line) <= width:
            return line
        parts = [line[i : i + width] for i in range(0, len(line), width)]
        return '\r\n '.join(parts)

    @classmethod
    def parse_datetime(cls, value: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse a human date/time and return canonical representations.

        Returns a dict with keys:
          - 'iso': ISO-8601 string (if parsed)
          - 'ical': RFC5545 value string (DATE or DATE-TIME with Z if UTC)
          - 'is_date': True if parsed as a date-only value
          - 'dt': the parsed datetime object

        Returns None if parsing fails.
        """
        if not value:
            return None
        try:
            # dateutil can parse many freeform date/time strings
            dt = dateparser.parse(value, fuzzy=True)
        except Exception:
            return None

        if dt is None:
            return None

        is_date = bool(cls.DATE_ONLY_RE.match(value.strip())) or (dt.hour == 0 and dt.minute == 0 and dt.second == 0 and '\n' not in value)
        iso = dt.isoformat()

        # RFC5545 formats
        if is_date:
            ical = dt.strftime("%Y%m%d")
        else:
            # if tz-aware and UTC, append Z
            if dt.tzinfo is not None:
                try:
                    offset = dt.utcoffset()
                    if offset is not None and offset.total_seconds() == 0:
                        ical = dt.strftime("%Y%m%dT%H%M%SZ")
                    else:
                        ical = dt.strftime("%Y%m%dT%H%M%S")
                except Exception:
                    ical = dt.strftime("%Y%m%dT%H%M%S")
            else:
                ical = dt.strftime("%Y%m%dT%H%M%S")

        return {"iso": iso, "ical": ical, "is_date": is_date, "dt": dt}

    @staticmethod
    def normalize_uid(value: Optional[str] = None, domain: Optional[str] = None) -> str:
        """Return a UID; generate one when not provided."""
        if value:
            return value
        dom = domain or "infracalendar.local"
        return f"{uuid.uuid4()}@{dom}"

    @staticmethod
    def normalize_geo(value: Optional[str]) -> Optional[str]:
        """Normalize latitude/longitude to 'lat;lon' format.

        Accepts 'lat,lon' or 'lat;lon' or 'lat lon'.
        """
        if not value:
            return None
        v = value.strip()
        v = v.replace(",", ";")
        v = v.replace(" ", ";")
        parts = [p for p in v.split(";") if p]
        if len(parts) < 2:
            return None
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            return f"{lat};{lon}"
        except Exception:
            return None

    @staticmethod
    def normalize_categories(value: Optional[str]) -> List[str]:
        if not value:
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        return [c.strip() for c in re.split(r",|;", value) if c.strip()]

    @staticmethod
    def normalize_attendees(value: Optional[Any]) -> List[str]:
        """Normalize attendees into cal-addresses (mailto:...)"""
        if not value:
            return []
        items = []
        if isinstance(value, str):
            # comma-separated
            parts = [p.strip() for p in re.split(r",|;", value) if p.strip()]
        elif isinstance(value, list):
            parts = [str(p).strip() for p in value if p]
        else:
            parts = [str(value).strip()]

        for p in parts:
            if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", p):
                items.append(f"mailto:{p}")
            else:
                items.append(p)
        return items

    @staticmethod
    def normalize_duration(value: Optional[Any]) -> Optional[str]:
        """Normalize durations to RFC5545 DURATION (e.g., 'PT1H30M').

        Accepts integer seconds, timedelta, or simple strings like '1h 30m'.
        Returns None if unable to normalize.
        """
        if value is None:
            return None
        if isinstance(value, timedelta):
            secs = int(value.total_seconds())
        elif isinstance(value, int):
            secs = value
        else:
            s = str(value).strip().lower()
            # quick parse like '1h 30m' or '90m'
            m = re.findall(r"(?:(\d+)\s*d)?\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?", s)
            if m:
                d, h, mm, sec = m[0]
                secs = (int(d or 0) * 86400) + (int(h or 0) * 3600) + (int(mm or 0) * 60) + (int(sec or 0))
            else:
                # if already looks like P... return as is
                if s.startswith("p") or s.startswith("pt"):
                    return s.upper()
                return None

        # build PnDTnHnMnS (use PT if no days)
        days, rem = divmod(secs, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        parts = []
        if days:
            parts.append(f"{days}D")
        time_parts = []
        if hours:
            time_parts.append(f"{hours}H")
        if minutes:
            time_parts.append(f"{minutes}M")
        if seconds:
            time_parts.append(f"{seconds}S")
        if time_parts:
            parts.append("T" + "".join(time_parts))

        return "P" + "".join(parts) if parts else None


if __name__ == "__main__":
    # quick demo
    demo_text = "Line1, second;third\nnext"
    print("escaped:", IcalNormalizer.normalize_text(demo_text))
    print("folded:", IcalNormalizer.fold_line("A" * 160))
    print("uid:", IcalNormalizer.normalize_uid(domain="example.com"))
    print("parse dt:", IcalNormalizer.parse_datetime("January 10 2026 10:00 AM EST"))
    print("geo:", IcalNormalizer.normalize_geo("37.4,-122.0"))
    print("att:", IcalNormalizer.normalize_attendees("alice@example.com;Bob <bob@example.com>"))