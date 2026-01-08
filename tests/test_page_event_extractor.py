from app.services.page_event_extractor import PageEventExtractor
from app.domain.page import Page


def test_extract_events_from_vevent_block():
    # Use free-form text example (NLP + date extraction) instead of VEVENT block
    text = """
Test Event
Join us at Test Park on January 10, 2026 at 10:00 AM
This is a test
"""
    page = Page(page_id=1, page_url="https://example.com", http_status=200, fetched_at=None, config_id=None, plain_text=text)
    ev = PageEventExtractor.extract_events(page)
    assert ev is not None
    assert ev.summary == "Test Event"
    assert ev.dtstart is not None
    # location should be detected by the NLP fallback
    assert ev.location is not None


def test_extract_events_fallback_date_line():
    text = "\nFun Hike\nJanuary 10, 2026 10:00 AM\nJoin us for a hike"
    page = Page(page_id=2, page_url="https://example.com", http_status=200, fetched_at=None, config_id=None, plain_text=text)
    ev = PageEventExtractor.extract_events(page)
    assert ev is not None
    assert ev.dtstart is not None
    assert ev.url == "https://example.com"
