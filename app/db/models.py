from __future__ import annotations

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Page(Base):
    __tablename__ = "pages"

    page_id = Column(Integer, primary_key=True)
    page_url = Column(Text, unique=True, nullable=False)
    page_content = Column(Text, nullable=True)
    plain_text = Column(Text, nullable=True)
    http_status = Column(Integer, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    config_id = Column(Integer, nullable=True)
