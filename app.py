#!/usr/bin/env python3
import argparse
import json
import logging
import re
from typing import Any, Dict, List

import requests
from dateutil import parser as dateparser

logging.basicConfig(level=logging.INFO, format="%(message)s")


ISO8601_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def fetch_openapi(spec_url: str, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    resp = requests.get(spec_url, timeout=10, headers=headers)
    resp.raise_for_status()
    return resp.json()


def find_crawlers_export(spec: Dict[str, Any], endpoint_path: str = "/crawlers/export"):
    paths = spec.get("paths", {})
    # try exact match first
    if endpoint_path in paths:
        return list(paths[endpoint_path].keys())[0], endpoint_path
    # try without leading slash
    no_lead = endpoint_path.lstrip("/")
    for p in paths:
        if p.endswith(no_lead) or p == f"/{no_lead}":
            methods = list(paths[p].keys())
            return methods[0], p
    return None, endpoint_path


def call_endpoint(base_url: str, path: str, method: str = "get", headers: Dict[str, str] | None = None):
    url = base_url.rstrip("/") + path if path.startswith("/") else base_url.rstrip("/") + "/" + path
    method = method.lower()
    logging.info(f"Calling {method.upper()} {url}")
    if method == "get":
        resp = requests.get(url, timeout=30, headers=headers)
    elif method == "post":
        resp = requests.post(url, timeout=30, headers=headers)
    else:
        resp = requests.request(method, url, timeout=30, headers=headers)
    resp.raise_for_status()
    # attempt JSON, fall back to text
    try:
        return resp.json()
    except ValueError:
        return resp.text


def looks_like_iso(s: str) -> bool:
    return bool(ISO8601_RE.search(s))


def parse_possible_date(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return False
    if isinstance(value, str):
        if "BEGIN:VCALENDAR" in value:
            return True
        if looks_like_iso(value):
            try:
                dateparser.parse(value)
                return True
            except Exception:
                return False
    return False


def is_calendar_event_obj(obj: Dict[str, Any]) -> bool:
    # look for datetime-like keys and event-like keys
    datetime_keys = 0
    event_keys = 0
    common_event_keys = {"start", "end", "start_time", "end_time", "dtstart", "dtend", "date", "datetime"}
    for k, v in obj.items():
        lk = k.lower()
        if lk in common_event_keys or "time" in lk or "date" in lk:
            if parse_possible_date(v):
                datetime_keys += 1
        if lk in {"summary", "title", "description", "location", "name", "subject"}:
            event_keys += 1
    # heuristics: at least one datetime-like and one event-like OR two datetime-like
    return (datetime_keys >= 1 and event_keys >= 1) or (datetime_keys >= 2)


def inspect_response(resp: Any) -> List[Dict[str, Any]]:
    events = []
    # if text, check for ICS
    if isinstance(resp, str):
        if "BEGIN:VCALENDAR" in resp:
            events.append({"raw_ics": resp})
        return events

    # if JSON
    if isinstance(resp, dict):
        # common wrapper keys
        for key in ("events", "items", "results", "data"):
            if key in resp and isinstance(resp[key], list):
                resp_list = resp[key]
                for item in resp_list:
                    if isinstance(item, dict) and is_calendar_event_obj(item):
                        events.append(item)
                if events:
                    return events
        # maybe single object that is an event
        if is_calendar_event_obj(resp):
            events.append(resp)
        return events

    if isinstance(resp, list):
        for item in resp:
            if isinstance(item, dict) and is_calendar_event_obj(item):
                events.append(item)
            elif isinstance(item, str) and "BEGIN:VCALENDAR" in item:
                events.append({"raw_ics": item})
        return events

    return events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-url", default="http://localhost:8002/openapi.json")
    parser.add_argument("--endpoint", default="/crawlers/export")
    parser.add_argument("--base-url", default="http://localhost:8002")
    parser.add_argument("--auth-header", help='Raw header, e.g. "Authorization: Bearer <token>"')
    parser.add_argument("--bearer-token", help='Shortcut to set Authorization: Bearer <token>')
    args = parser.parse_args()
    # build headers
    headers: Dict[str, str] = {}
    if args.bearer_token:
        headers["Authorization"] = f"Bearer {args.bearer_token}"
    elif args.auth_header:
        if ":" in args.auth_header:
            k, v = args.auth_header.split(":", 1)
            headers[k.strip()] = v.strip()
        else:
            headers["Authorization"] = args.auth_header.strip()

    try:
        spec = fetch_openapi(args.spec_url, headers=headers if headers else None)
        method, path = find_crawlers_export(spec, args.endpoint)
        if method is None:
            logging.info("/crawlers/export path not found in spec; defaulting to GET")
            method = "get"
            path = args.endpoint
        data = call_endpoint(args.base_url, path, method, headers=headers if headers else None)
        events = inspect_response(data)
        if events:
            logging.info(f"Found {len(events)} calendar-like item(s)")
            with open("events_found.json", "w") as fh:
                json.dump(events, fh, indent=2, default=str)
            logging.info("Wrote events_found.json")
        else:
            logging.info("No calendar events detected in response.")
    except Exception as e:
        logging.error(f"Error: {e}")


if __name__ == "__main__":
    main()
