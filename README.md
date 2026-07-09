# Composio AI Research Agent

A modular, AI-powered research system for analyzing SaaS applications and determining their buildability for AI agents. This project demonstrates clean architecture, modular design, maintainability, and AI-first engineering practices.

## Project Overview

The AI Research Agent is designed to analyze 100 SaaS applications and extract structured information including:

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

## Objective

Build a production-ready research system that:

1. **Discovers** SaaS applications from curated lists
2. **Researches** each application using AI/LLM-powered analysis
3. **Verifies** research data for accuracy and quality
4. **Analyzes** patterns and generates insights
5. **Presents** findings in an interactive dashboard

## Folder Structure

```
project-root/
│
├── agent/                          # Python backend
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # Main orchestrator and CLI entry point
│   ├── config.py                   # Configuration management (dotenv)
│   ├── logger.py                   # Logging utility (Rich)
│   ├── models.py                   # Pydantic data models
│   ├── utils.py                    # Utility functions (JSON, CSV, retry, etc.)
│   ├── prompts.py                  # LLM prompt templates
│   ├── analyzer.py                 # Analytics engine (skeleton)
│   ├── verifier.py                 # Verification module (skeleton)
│   └── apps.json                   # List of 100 SaaS applications
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
│   ├── script.js                   # Dashboard logic
│   └── assets/                     # Static assets
│
├── docs/                           # Documentation
├── screenshots/                    # Screenshots for README
│
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
└── LICENSE                         # License file
```

## Planned Workflow

### 1. Application Discovery
- Load application list from `agent/apps.json`
- Validate application names and URLs
- Prepare research queue

### 2. Research Phase
- Fetch website content using Playwright/Requests
- Extract information using LLM (OpenAI/Anthropic)
- Structure data using Pydantic models
- Save raw research data to `output/raw/`

### 3. Verification Phase
- Validate research data completeness
- Cross-reference with multiple sources
- Calculate quality and confidence scores
- Update verification status
- Save verified data to `output/verified/`

### 4. Analytics Phase
- Generate category statistics
- Analyze authentication patterns
- Assess buildability insights
- Calculate confidence metrics
- Generate comprehensive reports

### 5. Dashboard Presentation
- Load verified data
- Render interactive charts
- Display filterable table
- Show detailed application views
- Export analytics

## Tech Stack

### Backend
- **Python 3.12+** - Core language
- **Pydantic** - Data validation and models
- **Pandas** - Data manipulation and analysis
- **Requests** - HTTP requests
- **BeautifulSoup4** - Web scraping
- **Playwright** - Browser automation
- **Rich** - Beautiful console output
- **python-dotenv** - Environment configuration

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling with CSS variables
- **Vanilla JavaScript** - Dashboard logic
- **Chart.js** - Data visualization

### Deployment
- **GitHub Pages** - Frontend hosting
- **GitHub Repository** - Version control

## Architecture

### Design Principles

The project follows **SOLID principles** and **clean architecture**:

1. **Single Responsibility** - Each module has one clear purpose
2. **Open/Closed** - Easy to extend without modifying core logic
3. **Liskov Substitution** - Consistent interfaces across modules
4. **Interface Segregation** - Focused, cohesive interfaces
5. **Dependency Inversion** - Dependencies on abstractions, not concretions

### Module Responsibilities

#### Core Modules

**config.py** - Configuration Management
- Loads environment variables from `.env`
- Provides centralized settings access
- Manages output directories
- Prepares API key management for future providers

**logger.py** - Logging Utility
- Centralized logging with Rich
- Color-coded output (info, warning, error, success)
- Console and file logging support
- Structured log formatting

**models.py** - Data Models
- Pydantic models for type safety
- Validation and serialization
- Enums for controlled vocabularies
- Batch processing support

**utils.py** - Utility Functions
- JSON read/write operations
- CSV export functionality
- URL validation and normalization
- Retry mechanisms with exponential backoff
- Data transformation helpers

**prompts.py** - Prompt Templates
- Structured LLM prompts
- Prompt builder pattern
- System prompts for different roles
- Template management

#### Business Logic Modules

**analyzer.py** - Analytics Engine (Skeleton)
- Authentication statistics
- Category distribution analysis
- API surface statistics
- Buildability insights
- Confidence score analysis
- MCP support statistics
- Report generation

**verifier.py** - Verification Module (Skeleton)
- Data validation
- Cross-reference verification
- Quality scoring
- Consistency checks
- Batch verification
- Quality assurance

**main.py** - Main Orchestrator (Skeleton)
- Application discovery
- Research workflow
- Verification workflow
- Analytics workflow
- Data management
- Dashboard preparation
- CLI interface

### Data Flow

```
┌─────────────────┐
│  apps.json      │
│  (100 apps)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ResearchAgent  │
│  (main.py)      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌────────┐
│Research│ │Verify  │
│Phase  │ │Phase   │
└───┬───┘ └───┬────┘
    │         │
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
│  (analytics)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌────────┐
│Reports│ │Charts  │
└───┬───┘ └───┬────┘
    │         │
    └────┬────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │
│  (website/)     │
└─────────────────┘
```

## Future Implementation Plan

### Phase 1: Core Infrastructure (Current)
- ✅ Project structure setup
- ✅ Configuration management
- ✅ Logging system
- ✅ Data models with Pydantic
- ✅ Utility functions
- ✅ Prompt templates structure
- ✅ Frontend dashboard skeleton
- ✅ Documentation

### Phase 2: Research Implementation
- [ ] LLM provider integration (OpenAI/Anthropic)
- [ ] Web scraping with Playwright
- [ ] Research workflow implementation
- [ ] Data extraction and structuring
- [ ] Error handling and retries

### Phase 3: Verification & Quality
- [ ] Verification logic implementation
- [ ] Cross-reference checking
- [ ] Quality scoring algorithms
- [ ] Consistency validation
- [ ] Batch processing

### Phase 4: Analytics & Reporting
- [ ] Statistics calculation
- [ ] Report generation (JSON/CSV/HTML)
- [ ] Chart data preparation
- [ ] Insight generation
- [ ] Export functionality

### Phase 5: Dashboard Enhancement
- [ ] Real-time data loading
- [ ] Advanced filtering
- [ ] Interactive charts
- [ ] Export capabilities
- [ ] Responsive improvements

### Phase 6: Production Readiness
- [ ] Testing suite (pytest)
- [ ] CI/CD pipeline
- [ ] Error monitoring
- [ ] Performance optimization
- [ ] Documentation completion

## Code Quality Standards

This project maintains high code quality through:

- **Type Hints** - All functions and methods are typed
- **Docstrings** - Comprehensive documentation for all modules
- **Modular Architecture** - Separation of concerns
- **SOLID Principles** - Clean, maintainable design
- **Consistent Naming** - Clear, descriptive names
- **Error Handling** - Proper exception management
- **Logging** - Structured logging throughout
- **Validation** - Pydantic models for data integrity

## Getting Started

### Prerequisites

- Python 3.12 or higher
- pip package manager
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/MeghanaKotambari/composio-ai-research-agent.git
cd composio-ai-research-agent
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

5. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

### Usage

#### Command Line Interface

```bash
# Research applications
python -m agent.main research --input agent/apps.json --output output/raw

# Verify research data
python -m agent.main verify --input output/raw/apps.json --output output/verified

# Analyze verified data
python -m agent.main analyze --input output/verified/apps.json --output output/reports

# Generate dashboard data
python -m agent.main dashboard --input output/verified/apps.json --output website/data
```

#### Dashboard

Open `website/index.html` in a web browser to view the dashboard.

For GitHub Pages deployment, the dashboard will be available at:
`https://<username>.github.io/composio-ai-research-agent/`

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black agent/ website/
isort agent/ website/
```

### Type Checking

```bash
mypy agent/
```

### Linting

```bash
flake8 agent/
```

## Architecture Decisions

### Why This Architecture Supports Scalability and Maintainability

#### 1. **Modular Design**
Each module has a single responsibility, making it easy to:
- Understand individual components
- Test in isolation
- Update without affecting other modules
- Reuse across projects

#### 2. **Pydantic Models**
- Type safety prevents runtime errors
- Automatic validation ensures data integrity
- Easy serialization/deserialization
- Self-documenting code through field descriptions

#### 3. **Configuration Management**
- Centralized settings via dotenv
- Easy to switch between environments
- No hardcoded values
- Extensible for future API keys

#### 4. **Logging Strategy**
- Structured logging with Rich
- Different log levels for different contexts
- Easy debugging and monitoring
- Production-ready logging setup

#### 5. **Utility Functions**
- Reusable across modules
- Well-tested interfaces
- Consistent error handling
- Reduces code duplication

#### 6. **Prompt Management**
- Centralized prompt templates
- Easy to iterate on prompts
- Version control friendly
- Supports multiple LLM providers

#### 7. **Frontend Separation**
- Pure HTML/CSS/JS (no build step)
- Easy to deploy to GitHub Pages
- Fast development iteration
- No framework lock-in

#### 8. **Skeleton Pattern**
- Clear interfaces defined early
- Implementation can proceed in parallel
- Easy to track progress
- Reduces integration issues

#### 9. **Type Hints Everywhere**
- Better IDE support
- Catches errors early
- Self-documenting code
- Easier refactoring

#### 10. **Extensibility**
- Easy to add new LLM providers
- Simple to extend data models
- Pluggable verification strategies
- Flexible analytics engine

## Contributing

This is a take-home assignment project. Contributions are not expected but the architecture is designed to be:
- Easy to understand
- Simple to extend
- Ready for production enhancement

## License

MIT License - See LICENSE file for details

## Contact

Built for Composio AI Product Ops Intern Take-Home Assignment

---

**Note**: This project is currently in architecture setup phase. Research logic, verification algorithms, and analytics calculations will be implemented in future phases.