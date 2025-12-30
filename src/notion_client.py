from __future__ import annotations

import os
from typing import Dict, Any, Optional

import requests


NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"


def build_basic_props(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Conservative, portfolio-safe property mapping.
    Rename these to match your own Notion DB if you ever enable it.
    """
    props: Dict[str, Any] = {}

    if parsed.get("filament_g") is not None:
        props["Filament g"] = {"number": float(parsed["filament_g"])}

    if parsed.get("filament_mm") is not None:
        props["Filament mm"] = {"number": float(parsed["filament_mm"])}

    if parsed.get("time_seconds") is not None:
        props["Time (s)"] = {"number": int(parsed["time_seconds"])}

    if parsed.get("slicer"):
        props["Slicer"] = {"select": {"name": parsed["slicer"]}}

    # WARNING: source file paths can leak internal structure.
    # Keep it as filename only if you plan to publish your output.
    if parsed.get("source_file"):
        props["Source File"] = {"rich_text": [{"text": {"content": str(parsed["source_file"])}}]}

    return props


def create_usage_page(
    database_id: str,
    title: str,
    props: Dict[str, Any],
    notion_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a row (page) in a Notion database.

    Credentials are NEVER stored in code.
    Token must come from env var NOTION_TOKEN (or passed in at runtime).
    """
    token = notion_token or os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("Missing NOTION_TOKEN env var. Do not hardcode tokens.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            # Notion database must have a Title property called "Name"
            "Name": {"title": [{"text": {"content": title}}]},
            **props,
        },
    }

    resp = requests.post(NOTION_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()
