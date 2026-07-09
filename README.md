# Composio AI Research Agent

A modular, production-ready AI-powered research system for analyzing SaaS applications and determining their buildability for AI agents. Built for the Composio AI Product Ops Internship assignment.

## Problem

Product Operations teams need to evaluate 100+ SaaS applications for AI agent integration. Manual research is slow, inconsistent, and doesn't scale. This agent automates the entire pipeline:

1. **Documentation Discovery** — Finds official developer docs (not homepages)
2. **Web Research** — Fetches and extracts clean text from documentation
3. **LLM Extraction** — Uses AI to extract structured data (auth methods, API surface, buildability)
4. **Deterministic Verification** — Cross-references extracted data against documentation
5. **Analytics** — Generates insights, clusters, and opportunity matrices
6. **Dashboard** — Interactive HTML dashboard with charts and filters

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI (main.py)                          │
│              research | resume | status                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   ResearchAgent                             │
│         Orchestrates pipeline, manages state                │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   ResearchWorkflow                          │
│  Discover → Fetch → Extract → Prompt → LLM → Parse → Verify │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┬───┘
   │          │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Doc  │ │  Web   │ │Prompt│ │  LLM   │ │ Parser │ │Verifier│
│Discov│ │Research│ │Builder│ │Provider│ │        │ │        │
└──────┘ └────────┘ └──────┘ └────────┘ └────────┘ └────────┘
                              │
                              ▼
                         ┌────────┐
                         │  Cache │
                         │output/ │
                         │ cache/ │
                         └────────┘
```

## Workflow

```
Load Apps (107 SaaS apps)
    │
    ▼
Discover Documentation (dev docs > API docs > homepage)
    │
    ▼
Fetch Documentation (with disk cache in output/cache/)
    │
    ▼
Extract Text (BeautifulSoup, clean content)
    │
    ▼
Build Prompt (structured JSON extraction prompt)
    │
    ▼
Call LLM (Mock or OpenRouter provider)
    │
    ▼
Parse Response (JSON extraction, validation, repair)
    │
    ▼
Estimate Confidence (based on evidence, completeness, verification)
    │
    ▼
Verify (deterministic keyword matching, reuses cached docs)
    │
    ▼
Save Result (atomic writes, resume support)
    │
    ▼
Generate Reports (results.json, statistics.json, insights.json, clusters.json, manual_review.json)
    │
    ▼
Dashboard (interactive HTML with Chart.js)
```

## Verification

Verification is **deterministic** — no LLM calls are made during verification. Each field is cross-referenced against documentation using keyword matching:

| Field | Verification Method |
|-------|-------------------|
| Auth Methods | Keyword matching (OAuth, API Key, JWT, etc.) |
| API Surface | REST, GraphQL, Webhook, SDK, OpenAPI keywords |
| Self-Serve | Sign up, free trial, contact sales detection |
| MCP Support | MCP, Model Context Protocol keywords |
| Evidence URL | Domain validation (docs., api., developer.) |

Apps with low verification scores (< 40) are flagged for **manual review**.

## Analytics

The analytics engine generates:

- **results.json** — All app research data
- **statistics.json** — Auth, category, API, accessibility, MCP, buildability stats
- **insights.json** — Cross-category insights (e.g., "CRM platforms support OAuth")
- **clusters.json** — Blocker clustering (e.g., "No Public API", "Enterprise Only")
- **manual_review.json** — Apps needing human validation

## Dashboard

The interactive HTML dashboard (`website/index.html`) provides:

- Hero stats (total apps, verification rate, avg confidence)
- Executive insights
- Dashboard metrics (OAuth, API Keys, Self-Serve, etc.)
- Interactive charts (auth distribution, categories, API types, buildability)
- Opportunity matrix (easy wins, medium effort, high effort)
- Searchable/filterable data table
- Verification status
- Architecture diagram

All numbers come from real JSON data — no hardcoded statistics.

## How to Run

### Prerequisites

- Python 3.12+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/MeghanaKotambari/composio-ai-research-agent.git
cd composio-ai-research-agent

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure environment
cp .env.example .env
# Edit .env with your API keys if using OpenRouter
```

### Run Research

```bash
# Run with mock provider (no API key needed)
python -m agent.main research --provider mock --limit 10

# Run with OpenRouter (requires OPENROUTER_API_KEY in .env)
python -m agent.main research --provider openrouter --limit 10

# Force reprocess all apps
python -m agent.main research --provider mock --force

# Resume interrupted run
python -m agent.main resume

# Check status
python -m agent.main status
```

### View Dashboard

Open `website/index.html` in a browser after running research.

## How to Deploy

### Local Server

```bash
# Serve the website locally
python -m http.server 8000 --directory website
# Open http://localhost:8000
```

### Production

The agent can be deployed as a scheduled job (cron, GitHub Actions) to run research periodically. The dashboard is a static HTML file that can be served from any web server (Nginx, S3, GitHub Pages).

## Folder Structure

```
project-root/
│
├── agent/                          # Python backend
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # CLI entry point
│   ├── config.py                   # Configuration management
│   ├── logger.py                   # Logging utility (Rich)
│   ├── models.py                   # Pydantic data models
│   ├── utils.py                    # Utility functions
│   ├── storage.py                  # Research storage
│   ├── cache.py                    # Documentation cache
│   ├── web_research.py             # Web scraping
│   ├── prompt_builder.py           # LLM prompt generation
│   ├── parser.py                   # Response parsing
│   ├── verifier.py                 # Verification engine
│   ├── analyzer.py                 # Analytics engine
│   ├── workflow.py                 # Research workflow + doc discovery
│   ├── research_agent.py           # Main orchestrator
│   ├── llm/                        # LLM providers
│   │   ├── base.py                 # Base provider
│   │   ├── mock.py                 # Mock provider
│   │   ├── openrouter.py           # OpenRouter provider
│   │   └── factory.py              # Provider factory
│   └── apps.json                   # 107 SaaS applications
│
├── output/                         # Output directories
│   ├── raw/                        # Raw research data
│   ├── verified/                   # Verification reports
│   ├── reports/                    # Generated reports
│   │   ├── results.json
│   │   ├── statistics.json
│   │   ├── insights.json
│   │   ├── clusters.json
│   │   └── manual_review.json
│   └── cache/                      # Documentation cache
│
├── website/                        # Frontend dashboard
│   ├── index.html                  # Main dashboard page
│   ├── styles.css                  # Dashboard styles
│   └── script.js                   # Dashboard logic
│
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
└── LICENSE                         # License file
```

## Limitations

- **LLM Hallucinations** — Extracted data may contain inaccuracies. Always verify critical findings.
- **Manual Review Required** — Apps with low confidence or verification scores need human validation.
- **Enterprise Documentation** — Some apps require authentication to access developer docs.
- **Rate Limits** — Web research and LLM API calls are subject to rate limits.
- **Static Analysis** — Cannot capture dynamic API behavior or test endpoints.
- **Documentation Discovery** — Relies on common URL patterns; some apps use non-standard doc URLs.

## Future Work

- **Automatic Browser Agent** — Playwright-based browser automation for JavaScript-heavy sites
- **Parallel Research** — Concurrent processing of multiple applications
- **Continuous Monitoring** — Scheduled re-research to track API changes
- **MCP Discovery** — Automated detection of MCP support in documentation
- **Search Engine Discovery** — Use search APIs to find documentation when URL patterns fail
- **Export Formats** — CSV, Excel, PDF report exports
- **CI/CD Integration** — GitHub Actions workflow for automated research runs

## Tech Stack

### Backend
- **Python 3.12+** — Core language
- **Pydantic** — Data validation and models
- **Rich** — Beautiful console output
- **BeautifulSoup4** — Web scraping
- **python-dotenv** — Environment configuration
- **requests** — HTTP client

### Frontend
- **HTML5** — Structure
- **CSS3** — Dark theme with glassmorphism
- **Vanilla JavaScript** — Dashboard logic
- **Chart.js** — Data visualization

## License

MIT License — See LICENSE file for details

## Author

Built for Composio AI Product Ops Intern Take-Home Assignment