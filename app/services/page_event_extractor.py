from app.domain.event import Event
from app.services.page_nlp_service import PageNLPService
from app.services.page_date_service import PageDateService
from app.domain.page import Page


class PageEventExtractor:
  """Extract a single Event from a `Page` by delegating to NLP and date services.

  Returns an `Event` instance when a sensible start time is found, otherwise `None`.
  """

  @classmethod
  def extract_events(cls, page: Page) -> Event | None:
    text = page.plain_text if page is not None else None
    if not text:
      return None

    nlp_ctx = PageNLPService.extract(text)

    # Prefer NLP-detected date candidates; then parse them with PageDateService
    candidates = PageNLPService.extract_date_candidates(text)
    parsed_by_candidate = []
    for cand in candidates:
      found = PageDateService.find_dates(cand)
      if found:
        parsed_by_candidate.append({"candidate": cand, "found": found})

    # Prefer a candidate that looks like a "start" phrase
    start_keywords = ("start", "starts", "begin", "begins", "from", "starting", "kickoff")
    preferred_start_iso = None
    preferred_candidate = None
    for entry in parsed_by_candidate:
      cand_text = entry["candidate"].lower()
      if any(kw in cand_text for kw in start_keywords):
        preferred_candidate = entry
        break

    if preferred_candidate:
      first = preferred_candidate["found"][0]
      preferred_start_iso = first.get("dt")

    dates = []
    if parsed_by_candidate:
      for entry in parsed_by_candidate:
        for f in entry["found"]:
          dates.append(f)

    if not dates:
      dates = PageDateService.find_dates(text)

    # If we have a preferred start, return one Event
    if preferred_start_iso:
      ev = Event(
        uid=None,
        dtstamp=None,
        dtstart=preferred_start_iso,
        dtend=None,
        duration=None,
        summary=nlp_ctx.get("title"),
        description=nlp_ctx.get("description"),
        location=nlp_ctx.get("location"),
        url=page.page_url,
        raw=preferred_candidate["candidate"],
      )
      ev.title = ev.summary
      ev.start = ev.dtstart
      return ev

    # Otherwise, if any parsed dates exist, return the first as representative
    if dates:
      first = dates[0]
      ev = Event(
        uid=None,
        dtstamp=None,
        dtstart=first.get("dt") or first.get("text"),
        dtend=None,
        duration=None,
        summary=nlp_ctx.get("title"),
        description=nlp_ctx.get("description"),
        location=nlp_ctx.get("location"),
        url=page.page_url,
        raw=first.get("text"),
      )
      ev.title = ev.summary
      ev.start = ev.dtstart
      return ev

    return None


__all__ = ["PageEventExtractor"]
