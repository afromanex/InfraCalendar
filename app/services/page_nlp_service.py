import re
from typing import Optional, Dict, List


class PageNLPService:
    """Extract title, location, and description from page text.

    Uses spaCy NER and noun-chunking when available; otherwise falls back to
    regex and simple line-based heuristics. Methods are intentionally small
    so they are easy to test without spaCy installed.
    """

    SPACY_MODEL = None

    @classmethod
    def _load_spacy(cls):
        try:
            import spacy

            if cls.SPACY_MODEL is None:
                try:
                    cls.SPACY_MODEL = spacy.load("en_core_web_sm")
                except Exception:
                    # model not present; try to download (best-effort)
                    try:
                        from spacy.cli import download

                        download("en_core_web_sm")
                        cls.SPACY_MODEL = spacy.load("en_core_web_sm")
                    except Exception:
                        cls.SPACY_MODEL = None
            return cls.SPACY_MODEL
        except Exception:
            return None

    @classmethod
    def extract(cls, text: str) -> Dict[str, Optional[str]]:
        """Return {'title', 'location', 'description'} extracted from `text`."""
        if not text:
            return {"title": None, "location": None, "description": None}

        # try spaCy first
        nlp = cls._load_spacy()
        if nlp is not None:
            try:
                doc = nlp(text)
                # title: first heading-like line or first noun chunk
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                title = None
                if lines:
                    first = lines[0]
                    if len(first) < 200 and len(lines) > 1 and first.endswith((':', '-', '—')) is False:
                        title = first
                if not title:
                    nc = list(doc.noun_chunks)
                    title = nc[0].text if nc else None

                # location: prefer GPE/LOC/ORG entities
                location = None
                for ent in doc.ents:
                    if ent.label_ in ("GPE", "LOC", "FAC", "ORG"):
                        location = ent.text
                        break

                # description: first 1-2 sentences (excluding title)
                sents = list(doc.sents)
                desc = None
                if sents:
                    if title and title.strip() and sents[0].text.strip().startswith(title.strip()):
                        desc = " ".join(s.text.strip() for s in sents[1:3]) or None
                    else:
                        desc = " ".join(s.text.strip() for s in sents[0:2])

                return {"title": title, "location": location, "description": desc}
            except Exception:
                # fall through to heuristic
                pass

        # Fallback heuristics
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        title = None
        description = None
        location = None

        if lines:
            # candidate title: first short line (like a header)
            for ln in lines[:3]:
                if 3 <= len(ln) <= 200:
                    title = ln
                    break
            if not title:
                title = lines[0]

            # description: next 1-2 non-empty lines after title
            try:
                idx = lines.index(title)
            except ValueError:
                idx = 0
            desc_lines = lines[idx + 1 : idx + 3]
            description = " ".join(desc_lines) if desc_lines else None

            # location: look for patterns ' at <place>' or ' in <place>' on the same or following lines
            combined = " ".join(lines[:6])
            m = re.search(r"\b(?:at|in)\s+([A-Z][A-Za-z0-9 &,\.-]{2,100})", combined)
            if m:
                location = m.group(1).strip()
            else:
                # fallback: look for common location words
                m2 = re.search(r"(Park|Center|Hall|Clubhouse|Gateway|Reservoir|Lake|Trail|Parkway|Auditorium)", combined, re.IGNORECASE)
                if m2:
                    # return a short substring around the match
                    span = m2.span()
                    before = combined[max(0, span[0] - 30) : span[1] + 30]
                    location = before.strip()

        return {"title": title, "location": location, "description": description}

    @classmethod
    def extract_date_candidates(cls, text: str) -> List[str]:
        """Return a list of substrings that likely contain date/time mentions.

        Strategy:
        - If spaCy is available, return detected `DATE` entities (or their sentences).
        - Otherwise, fallback to regex: return sentences/line substrings containing
          month names or numeric date patterns.
        """
        if not text:
            return []

        candidates: List[str] = []
        nlp = cls._load_spacy()
        if nlp is not None:
            try:
                doc = nlp(text)
                # collect DATE entities
                for ent in doc.ents:
                    if ent.label_ == "DATE":
                        cand = ent.text.strip()
                        if cand and cand not in candidates:
                            candidates.append(cand)
                # also consider sentences containing date entities
                if not candidates:
                    for sent in doc.sents:
                        if any(t.ent_type_ == "DATE" for t in sent):
                            s = sent.text.strip()
                            if s and s not in candidates:
                                candidates.append(s)
                return candidates
            except Exception:
                # fall through to regex fallback
                pass

        # Regex fallback: look for month names or numeric date patterns inside sentences/lines
        month_re = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\b", re.IGNORECASE)
        date_num_re = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")

        # split into sentences using simple punctuation heuristics
        pieces = re.split(r"[\n\.\!\?]+", text)
        for p in pieces:
            p = p.strip()
            if not p:
                continue
            if month_re.search(p) or date_num_re.search(p):
                # choose a short substring (the sentence) as candidate
                if p not in candidates:
                    candidates.append(p)

        return candidates


__all__ = ["PageNLPService"]
