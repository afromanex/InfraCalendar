InfraCalendar
===============

Purpose
-------
Small Python CLI that fetches `http://localhost:8002/openapi.json`, locates the `/crawlers/export` endpoint, calls it, and inspects responses to identify calendar events.

Install
-------
Create a virtualenv and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Usage
-----
Run the script (defaults target localhost:8002):

```bash
python app.py
```

Options:
- `--spec-url`: OpenAPI JSON URL (default `http://localhost:8002/openapi.json`)
- `--endpoint`: endpoint path to call (default `/crawlers/export`)
- `--base-url`: base server URL (default `http://localhost:8002`)

Output
------
Prints a short summary of whether calendar-like items were found and writes `events_found.json` when events are detected.

Docker
------
Build the image:

```bash
docker build -t infracalendar:latest .
```

Run the container (Linux):

```bash
# Use host networking so the container can reach services on the host's localhost:8002
docker run --rm --network=host infracalendar:latest
```

Alternate (if your Docker supports `host.docker.internal`):

```bash
docker run --rm --add-host=host.docker.internal:host-gateway infracalendar:latest
```

Pass CLI args through the container:

```bash
docker run --rm --network=host infracalendar:latest --spec-url http://localhost:8002/openapi.json --endpoint /crawlers/export
```

Notes:
- On Linux, use `--network=host` to allow the container to access host `localhost` services; otherwise point the container at the host IP or use `host.docker.internal` if available.
- The container image uses `app.py` as the entrypoint and accepts the same CLI flags as the script.

Authentication:
- Pass a raw header with `--auth-header 'Authorization: Bearer <token>'`.
- Or use `--bearer-token <token>` as a shortcut.

Example (using your token):

```bash
docker run --rm --network=host infracalendar:latest --auth-header "Authorization: Bearer secret"
```

Be careful not to expose secrets in shared logs or CI history.
