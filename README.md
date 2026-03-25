# vc-signal-scanner

A thesis-driven startup signal monitor built for European venture capital. It scans multiple data sources, scores each signal against configurable investment theses using an LLM, and delivers a daily digest of the most relevant opportunities.

## Why This Exists

Most VC sourcing tools (Harmonic, Grata, etc.) offer a broad firehose of startup data. They're powerful but generic. **vc-signal-scanner** takes a different approach: it starts with *your fund's specific thesis* and works backward to find signals that match.

This is especially valuable for:
- **European-focused funds** where DACH/CEE ecosystems are underindexed by US-centric platforms
- **Post-PMF investors** who need traction signals, not just launch announcements
- **Small teams** that can't justify $20-50k/year for enterprise sourcing tools

## How It Works

```
Data Sources          Scoring Engine          Output
─────────────        ──────────────          ──────
Hacker News    ──┐
Product Hunt   ──┤                         ┌─ Markdown Report
GitHub Trend.  ──┼──▶  Claude API   ──▶────┤
RSS Feeds      ──┤     (thesis-aware        └─ Slack Webhook
Crunchbase     ──┘      scoring)
```

1. **Ingest** — pulls fresh signals from multiple startup-relevant sources
2. **Score** — an LLM evaluates each signal against your investment thesis (defined in plain English)
3. **Filter** — only high-relevance signals pass through (configurable threshold)
4. **Deliver** — outputs a daily digest as markdown or pushes to Slack

## Quick Start

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/vc-signal-scanner.git
cd vc-signal-scanner
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run
python main.py

# Run with custom thesis
python main.py --thesis theses/3vc_default.yaml

# Output to Slack
python main.py --slack
```

## Configuration

### Investment Thesis

Theses are defined in YAML — plain English that the LLM uses to evaluate relevance:

```yaml
fund_name: "3VC"
thesis:
  stage: "Post product-market fit, typically Series A"
  geography: "Founders from DACH and CEE regions, companies with global ambition"
  sectors:
    - "AI and machine learning infrastructure"
    - "Developer tools and platforms"
    - "Deep tech with commercial applications"
    - "Cybersecurity"
    - "Digital health"
    - "Data and analytics"
  signals:
    positive:
      - "Strong revenue growth or clear monetization"
      - "Expanding engineering team (hiring signals)"
      - "European founding team with global product"
    negative:
      - "Pre-product, idea stage only"
      - "Consumer social / ad-dependent model"
      - "No clear technical differentiation"
```

### Data Sources

Each source can be enabled/disabled in `config.yaml`:

```yaml
sources:
  hackernews:
    enabled: true
    min_score: 50          # minimum HN points to consider
    categories: ["show"]   # "show", "ask", "top", "new"
  producthunt:
    enabled: true
    min_votes: 100
  github:
    enabled: true
    languages: ["python", "typescript", "rust", "go"]
    min_stars_24h: 50
  rss:
    enabled: true
    feeds:
      - "https://tech.eu/feed/"
      - "https://sifted.eu/feed"
      - "https://www.eu-startups.com/feed/"
```

## Sample Output

See [`sample_output/`](./sample_output/) for example digests. Here's what a single entry looks like:

```
### Orderly — AI-powered supply chain optimization
🟢 Relevance: 8.5/10 | Source: Hacker News (Show HN, 142 pts)

Czech founding team building AI agents for supply chain planning.
Series A stage, claiming 3x revenue growth in 2025. B2B SaaS model
targeting mid-market European manufacturers.

**Why this fits 3VC:**
- CEE founders (Prague) with pan-European customer base
- Post-PMF with clear revenue traction
- AI/ML applied to a massive, underdigitized market
- Technical moat in domain-specific models

**Links:** [Website](https://example.com) | [HN Discussion](https://news.ycombinator.com/item?id=...)
```

## Architecture

```
vc-signal-scanner/
├── main.py                    # Entry point and CLI
├── config.yaml                # Source configuration
├── .env.example               # API keys template
├── requirements.txt
├── theses/
│   └── 3vc_default.yaml       # Investment thesis definition
├── src/
│   ├── models.py              # Data models (Signal, ScoredSignal)
│   ├── sources/               # Data ingestion modules
│   │   ├── hackernews.py
│   │   ├── producthunt.py
│   │   ├── github_trending.py
│   │   └── rss_feeds.py
│   ├── scoring/
│   │   └── thesis_scorer.py   # LLM-based thesis scoring
│   └── output/
│       ├── markdown_report.py # Markdown digest generator
│       └── slack_webhook.py   # Slack integration
└── sample_output/
    └── daily_digest_2026_03_25.md
```

## Adding New Sources

Each source implements a simple interface:

```python
from src.models import Signal

class MySource:
    async def fetch(self) -> list[Signal]:
        # Pull data from your source
        # Return a list of Signal objects
        ...
```

## Limitations & Roadmap

**Current limitations:**
- Scoring quality depends on the LLM's knowledge of the companies (works best for companies with public presence)
- Rate limits on free APIs constrain how much data can be pulled daily
- No persistent storage — each run is stateless

**Possible extensions:**
- [ ] Database for historical tracking and deduplication
- [ ] Web dashboard for browsing signals
- [ ] Email digest option
- [ ] Integration with Airtable/Notion for pipeline tracking
- [ ] Founder network analysis (co-founder backgrounds, prior exits)
- [ ] Traction signals via SimilarWeb API or app store rankings

## License

MIT
