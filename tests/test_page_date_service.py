from app.services.page_date_service import PageDateService


def test_find_dates_simple():
    text = "Join us on January 10, 2026 at 10:00 AM for the Fun Hike"
    res = PageDateService.find_dates(text)
    assert len(res) >= 1
    first = res[0]
    assert "January 10" in first["text"] or "2026" in first["text"]
    assert first["dt"] is not None


def test_find_dates_multiple():
    text = "Event A: Jan 10, 2026\nEvent B: Feb 2, 2026 14:00"
    res = PageDateService.find_dates(text)
    assert len(res) >= 2
    assert all(r["dt"] is not None for r in res)
