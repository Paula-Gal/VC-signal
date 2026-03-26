"""Reddit data source — startup and tech subreddits via the public JSON API."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from src.models import Signal, SourceType

logger = logging.getLogger(__name__)

DEFAULT_SUBREDDITS = ["startups", "SaaS", "MachineLearning", "artificial", "devops"]


class RedditSource:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.subreddits = self.config.get("subreddits", DEFAULT_SUBREDDITS)
        self.min_score = self.config.get("min_score", 20)
        self.max_items_per_sub = self.config.get("max_items_per_sub", 15)

    async def fetch(self) -> list[Signal]:
        """Fetch hot posts from configured subreddits."""
        signals = []
        headers = {"User-Agent": "vc-signal-scanner/1.0"}

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for sub in self.subreddits:
                try:
                    resp = await client.get(
                        f"https://www.reddit.com/r/{sub}/hot.json?limit={self.max_items_per_sub}",
                        headers=headers,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    for post in data.get("data", {}).get("children", []):
                        p = post.get("data", {})
                        score = p.get("score", 0)
                        if score < self.min_score or p.get("stickied"):
                            continue

                        url = p.get("url", "")
                        # Skip Reddit-internal links (text posts link back to Reddit)
                        if "reddit.com" in url:
                            url = f"https://www.reddit.com{p.get('permalink', '')}"

                        signals.append(Signal(
                            title=p.get("title", ""),
                            description=(p.get("selftext", "") or "")[:400],
                            source=SourceType.REDDIT,
                            url=url,
                            score=score,
                            author=p.get("author"),
                            tags=[sub.lower()],
                            discovered_at=datetime.utcfromtimestamp(p.get("created_utc", 0)),
                            extra={
                                "subreddit": sub,
                                "num_comments": p.get("num_comments", 0),
                                "reddit_url": f"https://www.reddit.com{p.get('permalink', '')}",
                            },
                        ))
                except httpx.HTTPError as e:
                    logger.warning(f"Reddit fetch failed for r/{sub}: {e}")

        logger.info(f"Reddit: fetched {len(signals)} posts across {len(self.subreddits)} subreddits")
        return signals
