#!/usr/bin/env python3
"""
Exports the current Overleaf browser session from `./browser_data`
into a portable `storage_state.json` and a base64 string.

This allows deploying the MCP server to cloud services (Railway, Render, Fly.io, Docker)
by simply setting the `OVERLEAF_STORAGE_STATE_B64` environment variable!
"""

import asyncio
import base64
import json
from pathlib import Path
from playwright.async_api import async_playwright
from config import OVERLEAF_PROFILE_DIR, BASE_DIR

OUTPUT_FILE = BASE_DIR / "storage_state.json"

async def export_session():
    print("Exporting authenticated Overleaf session...")
    if not OVERLEAF_PROFILE_DIR.exists():
        print(f"Error: Profile directory '{OVERLEAF_PROFILE_DIR}' not found.")
        print("Please run './setup_auth.py' first.")
        return

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(OVERLEAF_PROFILE_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )

        # Save storage state (cookies + localStorage)
        await context.storage_state(path=str(OUTPUT_FILE))
        await context.close()

    raw_json = OUTPUT_FILE.read_text(encoding="utf-8")
    b64_str = base64.b64encode(raw_json.encode("utf-8")).decode("utf-8")

    print("\n" + "=" * 65)
    print("✅ SESSION EXPORTED SUCCESSFULLY!")
    print("=" * 65)
    print(f"1. Saved to file: {OUTPUT_FILE}")
    print("\n2. Base64 String for Cloud Environment Variables:")
    print("   Set this in Railway/Render/Fly.io as 'OVERLEAF_STORAGE_STATE_B64':")
    print("-" * 65)
    print(b64_str)
    print("-" * 65)

if __name__ == "__main__":
    asyncio.run(export_session())
