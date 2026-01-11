import os
try:
	from dotenv import load_dotenv
	load_dotenv()
except Exception:
	# python-dotenv not installed in this environment; rely on environment variables
	pass

DATABASE_URL = os.getenv("DATABASE_URL")
