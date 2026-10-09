#!/usr/bin/env python3
"""
Overleaf One-Time Authentication Setup

Launches a visible Chromium browser with your persistent session profile.
Log in to Overleaf (via Email, Google, SSO, etc.).
Once you are logged into your dashboard, press Enter in the terminal.
Your session and cookies will be saved for all subsequent MCP calls!
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from config import OVERLEAF_PROFILE_DIR

async def setup_auth():
    print("=" * 60)
    print("OVERLEAF MCP - ONE-TIME LOGIN SETUP")
    print("=" * 60)
    print(f"Profile directory: {OVERLEAF_PROFILE_DIR}")
    print("Opening browser window to Overleaf...")
    print("Please log in to your Overleaf account.")
    print("=" * 60)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(OVERLEAF_PROFILE_DIR),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            viewport={"width": 1280, "height": 800},
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://www.overleaf.com/login", wait_until="domcontentloaded")

        print("\nBrowser is open! Log in now.")
        print("When you reach the Overleaf dashboard (https://www.overleaf.com/project),")
        
        # We can also monitor the URL automatically
        async def monitor_url():
            while True:
                try:
                    if "/project" in page.url and "/login" not in page.url:
                        print(f"\n[Detected Login] Current URL: {page.url}")
                        print("Authentication detected! You can now close or press Enter.")
                        break
                except Exception:
                    pass
                await asyncio.sleep(2)

        monitor_task = asyncio.create_task(monitor_url())

        # Wait for user input in non-blocking way
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input, "Press [ENTER] in this terminal once you have logged in to complete setup: ")
        
        monitor_task.cancel()
        print("\nSaving session and closing browser...")
        await context.close()
        print("Success! Your Overleaf session has been saved.")
        print("Claude can now automate Overleaf using this profile.")

if __name__ == "__main__":
    try:
        asyncio.run(setup_auth())
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        sys.exit(0)
