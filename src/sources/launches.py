"""Startup launch feeds — IndieHackers, BetaList, and similar early-stage launch platforms."""

from __future__ import annotations

import logging
from datetime import datetime

import feedparser
import httpx

from src.models import Signal, SourceType

logger = logging.getLogger(__name__)

LAUNCH_FEEDS = [
    "https://www.indiehackers.com",
    "https://betalist.com",
    "https://www.producthunt.com",
]


class LaunchesSource:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.feeds = self.config.get("feeds", LAUNCH_FEEDS)
        self.max_items_per_feed = self.config.get("max_items_per_feed", 20)
        self.max_age_hours = self.config.get("max_age_hours", 72)

    async def fetch(self) -> list[Signal]:
        """Fetch recent startup launches from all configured feeds."""
        signals = []

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for feed_url in self.feeds:
                try:
                    resp = await client.get(feed_url, headers={"User-Agent": "vc-signal-scanner/1.0"})
                    resp.raise_for_status()
                    feed = feedparser.parse(resp.text)
                    feed_title = feed.feed.get("title", feed_url)

                    for entry in feed.entries[: self.max_items_per_feed]:
                        try:
                            published = None
                            if hasattr(entry, "published_parsed") and entry.published_parsed:
                                published = datetime(*entry.published_parsed[:6])
                            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                                published = datetime(*entry.updated_parsed[:6])

                            if published:
                                age_hours = (datetime.utcnow() - published).total_seconds() / 3600
                                if age_hours > self.max_age_hours:
                                    continue

                            title = entry.get("title", "").strip()
                            if not title:
                                continue

                            description = ""
                            if hasattr(entry, "summary"):
                                description = self._strip_html(entry.summary)[:400]

                            signals.append(Signal(
                                title=title,
                                description=description,
                                source=SourceType.LAUNCHES,
                                url=entry.get("link", ""),
                                tags=["launch"],
                                discovered_at=published or datetime.utcnow(),
                                extra={"feed_title": feed_title},
                            ))
                        except Exception as e:
                            logger.debug(f"Error parsing launch entry: {e}")

                except Exception as e:
                    logger.warning(f"Launch feed failed ({feed_url}): {e}")

        logger.info(f"Launches: fetched {len(signals)} items from {len(self.feeds)} feeds")
        return signals

    @staticmethod
    def _strip_html(html_text: str) -> str:
        try:
            from bs4 import BeautifulSoup
            return BeautifulSoup(html_text, "html.parser").get_text(separator=" ", strip=True)
        except ImportError:
            import re
            return re.sub(r"<[^>]+>", "", html_text).strip()
