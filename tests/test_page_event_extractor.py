from app.services.page_event_extractor import PageEventExtractor


def test_extract_events_from_vevent_block():
    vevent = """
BEGIN:VEVENT
UID:1234@example.com
DTSTAMP:20260101T120000Z
DTSTART:20260110T100000Z
DTEND:20260110T120000Z
SUMMARY:Test Event
LOCATION:Test Park
DESCRIPTION:This is a test
END:VEVENT
"""
    events = PageEventExtractor.extract_events(vevent, page_url="https://example.com")
    assert len(events) == 1
    ev = events[0]
    assert ev.uid == "1234@example.com"
    assert ev.summary == "Test Event"
    assert ev.location == "Test Park"
    assert ev.dtstart is not None
    assert ev.dtend is not None


def test_extract_events_fallback_date_line():
    text = "\nFun Hike\nJanuary 10, 2026 10:00 AM\nJoin us for a hike"
    events = PageEventExtractor.extract_events(text, page_url="https://example.com")
    assert len(events) >= 1
    ev = events[0]
    assert ev.dtstart is not None
    assert ev.url == "https://example.com"
