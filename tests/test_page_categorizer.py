from app.services.page_categorizer import PageCategorizer


def test_is_calendar_with_date_text():
    text = "Join us on January 10, 2026 for the event"
    assert PageCategorizer.is_calendar(page=None, text=text) if hasattr(PageCategorizer.is_calendar, '__call__') else PageCategorizer.is_calendar(text)


def test_is_calendar_negative():
    text = "Welcome to our homepage with no dates"
    assert not PageCategorizer.is_calendar(page=None, text=text) if hasattr(PageCategorizer.is_calendar, '__call__') else not PageCategorizer.is_calendar(text)
