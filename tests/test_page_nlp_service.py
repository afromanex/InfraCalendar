from app.services.page_nlp_service import PageNLPService


def test_nlp_fallback_title_location_description():
    text = """
Fun Hike
Join us at Sippo Lake Park on January 10, 2026 for a family-friendly hike.
Meet at the north parking lot.
"""
    res = PageNLPService.extract(text)
    assert res["title"] is not None
    assert res["description"] is not None
    # fallback should detect 'Sippo Lake Park' as location
    assert res["location"] is not None
