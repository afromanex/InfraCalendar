import os
from app.clients.crawlers_client import CrawlersClient
from app.services.page_categorizer import PageCategorizer
from app.services.page_event_extractor import PageEventExtractor


def main():
	# token can be provided via AUTH_TOKEN env var (recommended)
	token = os.environ.get("AUTH_TOKEN", "secret")
	client = CrawlersClient(token=token)

	# call export with the requested config
	pages = client.export(config="starkparks.yml", include_html=False, include_plain_text=True, limit=100)
	calendar_pages = [p for p in pages if PageCategorizer.is_calendar(page=p)]
	print(f"Found {len(calendar_pages)} calendar-like page(s) out of {len(pages)} fetched")
	all_events = []
	for i, p in enumerate(calendar_pages, start=1):
		print(f"{i}. id={p.page_id} url={p.page_url} status={p.http_status}")
		events = PageEventExtractor.extract_events(p.plain_text, page_url=p.page_url)
		if events:
			print(f"   → {len(events)} extracted event(s):")
			for ev in events:
				print(f"     - title: {ev.title or '<no title>'}")
				print(f"       start: {ev.start}")
				print(f"       location: {ev.location}")
				if ev.description:
					desc = ev.description.strip().splitlines()[0]
					print(f"       description: {desc}...")
				else:
					print(f"       description: <none>")
				all_events.append({
					"page_id": p.page_id,
					"page_url": p.page_url,
					"title": ev.title,
					"start": ev.start,
					"location": ev.location,
					"description": ev.description,
					"raw": ev.raw,
				})
		else:
			print("   → no structured events extracted")

	if all_events:
		try:
			import json

			with open("events_found.json", "w") as fh:
				json.dump(all_events, fh, indent=2, default=str)
			print(f"Wrote {len(all_events)} events to events_found.json")
		except Exception as e:
			print(f"Failed to write events_found.json: {e}")


if __name__ == "__main__":
	main()

