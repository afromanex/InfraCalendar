import os
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.clients.crawlers_client import CrawlersClient
from app.repositories.pages import PagesRepository

router = APIRouter(prefix="/crawlers", tags=["Crawlers"])


@router.post("/fetch")
async def fetch_pages(
    config: str = Query(..., description="Config file name (e.g., starkparks.yml)"),
    include_html: bool = Query(False, description="Include HTML content"),
    include_plain_text: bool = Query(True, description="Include plain text"),
    limit: int = Query(100000, description="Max number of pages to fetch")
):
    """
    Fetch pages from the crawler service and save them to the database.
    """
    try:
        # Get crawler service configuration
        token = os.environ.get("AUTH_TOKEN", "secret")
        crawlers_url = os.environ.get("CRAWLERS_URL", "http://localhost:8002")
        
        # Initialize clients
        crawler_client = CrawlersClient(base_url=crawlers_url, token=token)
        pages_repo = PagesRepository()
        
        # Fetch pages from crawler
        pages = crawler_client.export(
            config=config,
            include_html=include_html,
            include_plain_text=include_plain_text,
            limit=limit
        )
        
        # Save pages to database
        saved_count = 0
        for page in pages:
            pages_repo.upsert_page(
                page_url=page.page_url,
                page_content=None if not include_html else page.page_content,
                http_status=page.http_status,
                fetched_at=page.fetched_at,
                config_id=page.config_id,
                plain_text=page.plain_text
            )
            saved_count += 1
        
        return {
            "status": "success",
            "message": f"Fetched and saved {saved_count} pages",
            "pages_saved": saved_count,
            "config": config
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pages: {str(e)}")
