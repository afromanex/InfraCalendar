import os
from app.clients.crawlers_client import CrawlersClient
from app.domain.event import Event
from app.repositories.pages import PagesRepository
from app.services.page_categorizer import PageCategorizer
from app.services.page_event_extractor import PageEventExtractor

def is_event(ev: Event) -> bool:
	if ev is None: 
		return False
	
	if ev.title is None or ev.start is None: 
		return False
	
	has_location = ev.location is not None 
	has_description = ev.description is not None and len(ev.description) >= 40

	return has_location or has_description

def main():
	# token can be provided via AUTH_TOKEN env var (recommended)
	token = os.environ.get("AUTH_TOKEN", "secret")
	crawlers_url = os.environ.get("CRAWLERS_URL", "http://localhost:8002")
	client = CrawlersClient(base_url=crawlers_url, token=token)
	pages_repo = PagesRepository()

	# call export with the requested config
	pages = client.export(
		config="starkparks.yml", 
		include_html=False, 
		include_plain_text=True, 
		limit=100000)

	for p in pages:
		# Save page to database
		pages_repo.upsert_page(
			page_url=p.page_url,
			page_content=None,  # not including HTML content
			http_status=p.http_status,
			fetched_at=p.fetched_at,
			config_id=p.config_id,
			plain_text=p.plain_text
		)
		
		ev = PageEventExtractor.extract_events(p)
		
		if is_event(ev):
			print(f"extracted event:")
			print(f" - url: {p.page_url}")
			print(f" - title: {ev.title}")
			print(f" - start: {ev.start}")
			print(f" - location: {ev.location}")
			print(f" - description: {ev.description}")
			print(f"")
		else: 
			print(f"no event extracted from page: {p.page_url}")
			print(f"")
		
if __name__ == "__main__":
	main()

