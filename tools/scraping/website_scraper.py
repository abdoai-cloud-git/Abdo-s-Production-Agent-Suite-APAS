"""Website scraping utility using httpx + BeautifulSoup."""

from __future__ import annotations

import os
from typing import Dict, Optional

import httpx
from bs4 import BeautifulSoup


class WebsiteScraper:
    """Fetches and sanitizes website content for downstream agents."""

    def __init__(self, *, timeout: float = 10.0, user_agent: Optional[str] = None) -> None:
        self.timeout = timeout
        self.user_agent = user_agent or "APASBot/1.0 (+https://abdo-agency.example)"

    def fetch(self, url: str, *, selector: Optional[str] = None, max_length: int = 4000) -> Dict[str, object]:
        headers = {"User-Agent": self.user_agent}
        with httpx.Client(headers=headers, timeout=self.timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        target = soup.select_one(selector) if selector else soup
        text = target.get_text(separator=" ", strip=True) if target else ""
        return {
            "url": url,
            "status_code": response.status_code,
            "title": soup.title.string.strip() if soup.title and soup.title.string else "",
            "content": text[:max_length],
        }


if __name__ == "__main__":
    target_url = os.getenv("SCRAPE_URL")
    if not target_url:
        print("Set SCRAPE_URL to run the website scraper demo.")
    else:
        scraper = WebsiteScraper()
        print(scraper.fetch(target_url, max_length=200))
