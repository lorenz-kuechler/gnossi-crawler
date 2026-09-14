#!/usr/bin/env python3
"""Check fgzzh.ch 'Freie Objekte' for new listings.

The listings on https://fgzzh.ch/freie-objekte/ are rendered client-side by an
embedded iframe (https://fgz.melon.rent/public-object-list), which in turn is a
Vue app that calls the melon.rent backend API directly. We talk to that API.
"""

import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

import requests
from dotenv import load_dotenv

API_URL = "https://api.ch.melon.rent/api/v1/objects/iframe-object-list"
TENANT_NAME = "fgz"
SOURCE_URL = "https://fgzzh.ch/freie-objekte/"

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "state" / "seen_ads.json"

load_dotenv(SCRIPT_DIR / ".env")

HEADERS = {
    "Tenant-Name": TENANT_NAME,
    "Accept": "application/json",
    "User-Agent": "gnossi-crawler/1.0 (+monitoring fgzzh.ch/freie-objekte for new listings)",
}


def fetch_all_items():
    items = []
    page = 1
    while True:
        resp = requests.get(
            API_URL,
            headers=HEADERS,
            params={"currentPage": page},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        page_items = data.get("items", [])
        items.extend(page_items)

        pagination = data.get("pagination", {})
        total_items = pagination.get("totalItems", len(items))
        if not page_items or len(items) >= total_items:
            break
        page += 1
    return items


def load_state():
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text())


def save_state(items_by_id):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(items_by_id, ensure_ascii=False, indent=2))


def describe(item):
    title = item.get("title") or "Objekt"
    address = item.get("address") or ""
    city = item.get("city") or ""
    location = ", ".join(p for p in (address, city) if p)
    link = f"https://fgz.melon.rent/public-object-details/{item.get('id')}"
    parts = [title]
    if location:
        parts.append(location)
    parts.append(link)
    return " - ".join(parts)


def send_email(new_ids, items_by_id):
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    mail_from = os.environ["MAIL_FROM"]
    mail_to = os.environ["MAIL_TO"]

    lines = [f"New ad(s) found on {SOURCE_URL}:", ""]
    lines += [f"- {describe(items_by_id[ad_id])}" for ad_id in sorted(new_ids)]
    body = "\n".join(lines)

    msg = MIMEText(body, "plain")
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg["Subject"] = f"fgzzh.ch: {len(new_ids)} neue Wohnungsinserat(e)"

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        server.send_message(msg)


def main():
    try:
        items = fetch_all_items()
    except requests.RequestException as exc:
        print(f"gnossi_crawler: failed to fetch {API_URL}: {exc}", file=sys.stderr)
        return 1

    items_by_id = {str(item["id"]): item for item in items if "id" in item}

    previous = load_state()
    save_state(items_by_id)

    if previous is None:
        print(
            f"gnossi_crawler: initialized baseline with {len(items_by_id)} ad(s), "
            "no comparison possible yet",
            file=sys.stderr,
        )
        return 0

    new_ids = set(items_by_id) - set(previous)
    if new_ids:
        print(f"New ad(s) found on {SOURCE_URL}:")
        for ad_id in sorted(new_ids):
            print(f"- {describe(items_by_id[ad_id])}")

        try:
            send_email(new_ids, items_by_id)
        except Exception as exc:
            print(f"gnossi_crawler: failed to send notification email: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
