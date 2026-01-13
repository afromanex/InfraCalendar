from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.clients.crawlers_client import CrawlersClient
from app.repositories.pages import PagesRepository


class CrawlersRouter:
    """Router for crawler service integration endpoints."""
    
    def __init__(
        self,
        crawler_client: CrawlersClient,
        pages_repo: PagesRepository
    ):
        """
        Initialize router with dependencies.
        
        Args:
            crawler_client: Client for communicating with crawler service
            pages_repo: Repository for persisting pages
        """
        self.crawler_client = crawler_client
        self.pages_repo = pages_repo
        self.router = APIRouter(prefix="/crawlers", tags=["Crawlers"])
        self._register_routes()
    
    def _register_routes(self):
        """Register all routes with the router."""
        self.router.add_api_route(
            "/fetch",
            self.fetch_pages,
            methods=["POST"]
        )
        self.router.add_api_route(
            "/remove_all_pages",
            self.remove_all_pages,
            methods=["DELETE"]
        )
    
    async def fetch_pages(
        self,
        config: str = Query(..., description="Config file name (e.g., starkparks.yml)"),
        include_html: bool = Query(False, description="Include HTML content"),
        include_plain_text: bool = Query(True, description="Include plain text"),
        limit: int = Query(100000, description="Max number of pages to fetch")
    ):
        """
        Fetch pages from the crawler service and save them to the database.
        """
        try:
            # Fetch pages from crawler
            pages = self.crawler_client.export(
                config=config,
                include_html=include_html,
                include_plain_text=include_plain_text,
                limit=limit
            )
            
            # Save pages to database
            saved_count = 0
            for page in pages:
                # Override config_id with the config name we used for fetching
                page.config_id = config
                self.pages_repo.upsert_page(page)
                saved_count += 1
            
            return {
                "status": "success",
                "message": f"Fetched and saved {saved_count} pages",
                "pages_saved": saved_count,
                "config": config
            }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching pages: {str(e)}")
    
    async def remove_all_pages(
        self,
        config: str = Query(..., description="Config name to remove all pages for (e.g., starkparks.yml)")
    ):
        """
        Remove all pages associated with a config from the database.
        """
        try:
            # Delete pages from database
            deleted_count = self.pages_repo.delete_pages_by_config_id(config)
            
            return {
                "status": "success",
                "message": f"Deleted {deleted_count} pages for config={config}",
                "pages_deleted": deleted_count,
                "config": config
            }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting pages: {str(e)}")


# Factory function to create router with dependencies from container
def create_crawlers_router(container) -> APIRouter:
    """Create and configure the crawlers router with dependencies from container."""
    crawlers_router = CrawlersRouter(
        crawler_client=container.crawlers_client(),
        pages_repo=container.pages_repository()
    )
    return crawlers_router.router


# Note: router is now initialized in main.py with container
router = None
