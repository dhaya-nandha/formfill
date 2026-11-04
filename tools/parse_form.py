import json
import sys

from playwright.sync_api import sync_playwright


def main():
    url = sys.argv[1]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)
            final, html = page.url, page.content()
            browser.close()
        print(json.dumps({"url": final, "html": html}))
    except Exception as e:
        print(json.dumps({"error": str(e)[:300]}))
        sys.exit(1)


if __name__ == "__main__":
    main()