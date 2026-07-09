# Composio AI Research Agent

A modular, AI-powered research system for analyzing SaaS applications and determining their buildability for AI agents. This project demonstrates clean architecture, modular design, maintainability, and AI-first engineering practices.

## Project Overview

The AI Research Agent analyzes 100+ SaaS applications and extracts structured information including:

- Application category and description
- Authentication methods
- Self-serve vs Gated access model
- API surface and capabilities
- MCP (Model Context Protocol) availability
- Buildability assessment for AI agents
- Main integration blockers
- Evidence URLs and confidence scores
- Verification status

The analyzed data is presented through an interactive HTML dashboard with charts, filters, and detailed views.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run research (with mock provider)
python -m agent.main research --provider mock --limit 10

# View dashboard
# Open website/index.html in browser
```

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
│   ├── web_research.py             # Web scraping
│   ├── prompt_builder.py           # LLM prompt generation
│   ├── parser.py                   # Response parsing
│   ├── verifier.py                 # Verification engine
│   ├── analyzer.py                 # Analytics engine
│   ├── workflow.py                 # Research workflow
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
│   ├── verified/                   # Verified research data
│   ├── reports/                    # Generated reports
│   └── charts/                     # Generated charts
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

## Implementation Status

### ✅ Fully Implemented

| Module | Description |
|--------|-------------|
| `config.py` | Configuration with dotenv, output directories |
| `logger.py` | Rich logging with color-coded output |
| `models.py` | Pydantic models for AppResearch, enums |
| `storage.py` | JSON storage with progress tracking |
| `web_research.py` | Documentation fetching with BeautifulSoup |
| `prompt_builder.py` | LLM prompt generation with JSON enforcement |
| `parser.py` | Response parsing with repair logic |
| `verifier.py` | Deterministic verification engine |
| `analyzer.py` | Analytics with insights and patterns |
| `workflow.py` | Research pipeline orchestration |
| `research_agent.py` | Main agent with resume support |
| `main.py` | CLI with Rich progress bars |
| `llm/` | Mock, OpenRouter, and factory providers |
| `website/` | Premium SaaS dashboard with Chart.js |

### 🟡 Partially Implemented

| Module | Description |
|--------|-------------|
| `apps.json` | 107 apps loaded (target was 100) |

## Architecture

### Design Principles

The project follows **SOLID principles** and **clean architecture**:

1. **Single Responsibility** - Each module has one clear purpose
2. **Open/Closed** - Easy to extend without modifying core logic
3. **Liskov Substitution** - Consistent interfaces across modules
4. **Interface Segregation** - Focused, cohesive interfaces
5. **Dependency Inversion** - Dependencies on abstractions, not concretions

### Data Flow

```
┌─────────────────┐
│  apps.json      │
│  (107 apps)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ResearchAgent  │
│  (orchestrator) │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌────────┐
│Workflow│ │Verify  │
│(fetch)│ │(deter- │
└───┬───┘ │ ministic)│
    │     └───┬────┘
    ▼         ▼
┌───────┐ ┌────────┐
│  Raw  │ │Verified│
│ Output│ │ Output │
└───┬───┘ └───┬────┘
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│   Analyzer      │
│  (insights)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │
│  (website/)     │
└─────────────────┘
```

## Key Features

### 1. Resume Support
- Progress saved after each app in `output/raw/processed.json`
- Interrupted runs can be resumed with `python -m agent.main resume`

### 2. Dependency Injection
- LLM providers injected via `LLMFactory`
- Research services can be swapped without code changes

### 3. Deterministic Verification
- No LLM calls during verification
- Keyword matching against documentation
- Apps flagged for manual review when needed

### 4. Pattern Detection
- Insights generated from cross-category analysis
- Opportunities categorized by effort level
- Blocker clustering for Product Ops

## Tech Stack

### Backend
- **Python 3.12+** - Core language
- **Pydantic** - Data validation and models
- **Rich** - Beautiful console output
- **BeautifulSoup4** - Web scraping
- **python-dotenv** - Environment configuration

### Frontend
- **HTML5** - Structure
- **CSS3** - Dark theme with glassmorphism
- **Vanilla JavaScript** - Dashboard logic
- **Chart.js** - Data visualization

## Limitations

- Possible LLM hallucinations in extracted data
- Need for manual review on low-confidence results
- Enterprise documentation may require authentication
- Rate limits on web research and LLM API calls
- Static analysis cannot capture dynamic API behavior

## Future Improvements

- Automatic browser agent (Playwright)
- Parallel research processing
- Continuous monitoring
- MCP discovery automation

## License

MIT License - See LICENSE file for details

## Contact

Built for Composio AI Product Ops Intern Take-Home Assignment