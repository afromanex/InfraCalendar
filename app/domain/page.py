from dataclasses import dataclass
from typing import Optional


@dataclass
class Page:
    page_id: Optional[int]
    page_url: Optional[str]
    http_status: Optional[int]
    fetched_at: Optional[str]
    config_id: Optional[int]
    plain_text: Optional[str]
