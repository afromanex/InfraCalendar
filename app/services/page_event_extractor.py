import re
from typing import List, Optional

from dateutil import parser as dateparser

from app.domain.event import Event


class PageEventExtractor:
    """Extract simple calendar-like events from raw page text.

    Heuristics implemented:
    - If the text contains an iCalendar VEVENT block, parse common properties.
    - Otherwise, scan for date-like lines and capture nearby lines as title/description.
    """

    VEVENT_RE = re.compile(r"BEGIN:VEVENT(.*?)END:VEVENT", re.DOTALL | re.IGNORECASE)
    # capture key (allow params like DTSTART;VALUE=DATE:) and the value after ':'
    FIELD_RE = re.compile(r"(?m)^(?P<key>[A-Z-]+)(?:;[^:]*)?:(?P<val>.*)$")
    DATE_LINE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\w*)\b", re.IGNORECASE)
    TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?:\s?[APMapm]{2})?\b")

    @classmethod
    def _try_parse_datetime(cls, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        try:
            dt = dateparser.parse(text, fuzzy=True)
            if dt:
                return dt.isoformat()
        except Exception:
            return None
        return None

    @classmethod
    def extract_events(cls, text: Optional[str], page_url: Optional[str] = None) -> List[Event]:
        if not text:
            return []
        events: List[Event] = []

        # 1) iCalendar VEVENT parsing
        for m in cls.VEVENT_RE.finditer(text):
            block = m.group(1)
            found = cls.FIELD_RE.findall(block)
            entries = {}
            for k, v in found:
                key = k.upper()
                entries.setdefault(key, []).append(v.strip())

            def single(k: str) -> Optional[str]:
                vals = entries.get(k)
                return vals[0] if vals else None

            uid = single("UID")
            dtstamp = cls._try_parse_datetime(single("DTSTAMP"))
            dtstart_raw = single("DTSTART")
            dtstart = cls._try_parse_datetime(dtstart_raw) or dtstart_raw
            dtend_raw = single("DTEND")
            dtend = cls._try_parse_datetime(dtend_raw) or dtend_raw
            duration = single("DURATION")
            summary = single("SUMMARY")
            description = single("DESCRIPTION")
            location = single("LOCATION")
            url = single("URL") or page_url
            categories = entries.get("CATEGORIES", [])
            status = single("STATUS")
            sequence = None
            try:
                seq_val = single("SEQUENCE")
                sequence = int(seq_val) if seq_val is not None else None
            except Exception:
                sequence = None

            created = cls._try_parse_datetime(single("CREATED"))
            last_modified = cls._try_parse_datetime(single("LAST-MODIFIED"))
            organizer = single("ORGANIZER")
            attendees = entries.get("ATTENDEE", [])
            rrule = single("RRULE")
            rdate = entries.get("RDATE", [])
            exdate = entries.get("EXDATE", [])

            ev = Event(
                uid=uid,
                dtstamp=dtstamp,
                dtstart=dtstart,
                dtend=dtend,
                duration=duration,
                summary=summary,
                description=description,
                location=location,
                url=url,
                categories=categories,
                status=status,
                sequence=sequence,
                created=created,
                last_modified=last_modified,
                organizer=organizer,
                attendees=attendees,
                rrule=rrule,
                rdate=rdate,
                exdate=exdate,
                raw=block.strip(),
            )

            # keep backward-compatible fields
            ev.title = summary
            ev.start = dtstart

            events.append(ev)

        if events:
            return events

        # 2) naive date-line based extraction
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for i, line in enumerate(lines):
            if cls.DATE_LINE_RE.search(line):
                title = lines[i - 1] if i > 0 else None
                desc_lines = lines[i + 1 : i + 4]
                description = "\n".join(desc_lines) if desc_lines else None

                # try to extract a date/time substring then parse
                date_match = cls.DATE_LINE_RE.search(line)
                time_match = cls.TIME_RE.search(line)
                candidate = None
                if date_match and time_match:
                    candidate = f"{date_match.group(0)} {time_match.group(0)}"
                elif date_match:
                    candidate = date_match.group(0)
                elif time_match:
                    candidate = time_match.group(0)

                start_iso = None
                if candidate:
                    start_iso = cls._try_parse_datetime(candidate)
                # fallback to try parsing entire line
                if not start_iso:
                    start_iso = cls._try_parse_datetime(line)

                ev = Event(
                    summary=title,
                    dtstart=start_iso or (candidate or line),
                    description=description,
                    raw=line,
                    url=page_url,
                )
                ev.title = title
                ev.start = ev.dtstart

                events.append(ev)

        return events
