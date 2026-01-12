"""Dependency injection container for the application."""
from dependency_injector import containers, providers


class Container(containers.DeclarativeContainer):
	"""Dependency injection container for the application."""
	
	# Configuration
	config = providers.Configuration()
	
	# Clients - Singleton to reuse connection pools
	ollama_client = providers.Singleton(
		"app.clients.ollama_client.OllamaClient"
	)
	
	# Repositories - Factory creates new instance per request
	pages_repository = providers.Factory(
		"app.repositories.pages.PagesRepository"
	)
	events_repository = providers.Factory(
		"app.repositories.events.EventsRepository"
	)
	
	# Services
	page_event_extractor = providers.Factory(
		"app.services.page_event_extractor.PageEventExtractor",
		ollama_client=ollama_client
	)
	
	page_event_service = providers.Factory(
		"app.services.page_event_extract_and_save.PageEventService",
		events_repository=events_repository,
		extractor=page_event_extractor
	)
	
	ical_formatting_service = providers.Singleton(
		"app.services.ical_formatting_service.ICalFormattingService"
	)
