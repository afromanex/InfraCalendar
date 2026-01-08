import pytest

from app.services.ical_normalizer import IcalNormalizer


def test_normalize_text_escapes():
    s = "Hello, World; Back\\slash\nNewline"
    out = IcalNormalizer.normalize_text(s)
    assert "\\," in out
    assert "\\;" in out
    assert "\\\\" in out
    assert "\\n" in out


def test_parse_datetime_iso_and_ical():
    res = IcalNormalizer.parse_datetime("2026-01-10 10:00")
    assert res is not None
    assert "iso" in res and "ical" in res
    assert res["iso"].startswith("2026-01-10")


def test_normalize_uid_generated():
    uid = IcalNormalizer.normalize_uid(domain="example.com")
    assert "@example.com" in uid


def test_normalize_geo():
    assert IcalNormalizer.normalize_geo("37.4,-122.0") == "37.4;-122.0"
    assert IcalNormalizer.normalize_geo("37.4 -122.0") == "37.4;-122.0"


def test_normalize_categories():
    assert IcalNormalizer.normalize_categories("one,two;three") == ["one", "two", "three"]


def test_normalize_attendees():
    at = IcalNormalizer.normalize_attendees("alice@example.com;bob@example.com")
    assert any(a.startswith("mailto:") for a in at)


def test_normalize_duration():
    assert IcalNormalizer.normalize_duration(3600) == "PT1H"
    assert IcalNormalizer.normalize_duration("1h 30m") == "PT1H30M"
