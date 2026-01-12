from fastapi import FastAPI
from app.routers import crawlers, extractors, calendars
from app.container import Container

# Initialize dependency injection container
container = Container()

# Initialize routers with dependencies from container
extractors.router = extractors.create_extractors_router(container)
calendars.router = calendars.create_calendars_router(container)

app = FastAPI(
    title="InfraCalendar API",
    description="API for fetching pages and extracting calendar events",
    version="1.0.0"
)

# Include routers
app.include_router(crawlers.router)
app.include_router(extractors.router)
app.include_router(calendars.router)


@app.get("/")
async def root():
    return {
        "message": "InfraCalendar API",
        "endpoints": {
            "fetch_pages": "/crawlers/fetch",
            "extract_events": "/extractors/extract",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

