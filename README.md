# ESG & Sustainability Analytics Platform

**Phase 1 — Foundation MVP**

An ESG analytics platform that centralizes environmental, social, and governance data, computes weighted ESG scores, and surfaces KPIs through an interactive Streamlit dashboard backed by a FastAPI REST API and PostgreSQL.

---

## Tech stack

| Layer | Technology |
|---|---|
| Dashboard | Streamlit 1.40, Plotly 5.24 |
| API | FastAPI 0.115, Uvicorn |
| Data processing | Pandas 2.2, NumPy 1.26 |
| Database | PostgreSQL 15, SQLAlchemy 2.0, Alembic |
| Configuration | Pydantic-settings, python-dotenv |
| Testing | Pytest, HTTPX |
| Deployment | Docker, Docker Compose, Railway |

---

## Project structure

```
ESG/
├── app/                        # FastAPI backend
│   ├── main.py                 # App entry point, router registration
│   ├── config.py               # Pydantic-settings configuration
│   ├── database.py             # SQLAlchemy engine + session factory
│   ├── models/                 # ORM table definitions
│   │   └── esg.py
│   ├── schemas/                # Pydantic request / response schemas
│   │   └── esg.py
│   ├── routers/                # Route handlers (one per ESG pillar)
│   │   ├── upload.py           # CSV / Excel ingestion endpoint
│   │   ├── environmental.py
│   │   ├── social.py
│   │   ├── governance.py
│   │   └── scoring.py
│   ├── services/               # Data pipeline (ingest → validate → transform)
│   │   ├── ingestion.py
│   │   ├── validator.py
│   │   └── transformer.py
│   ├── analytics/              # ESG computation modules
│   │   ├── environmental.py    # CO₂, energy, water, waste KPIs
│   │   ├── social.py           # Diversity, retention, engagement KPIs
│   │   ├── governance.py       # Compliance, risk, audit KPIs
│   │   └── scoring_engine.py   # Weighted ESG scoring (E 40 / S 30 / G 30)
│   └── utils/
│       └── helpers.py
├── dashboard/                  # Streamlit multi-page app
│   ├── main.py                 # Landing page
│   ├── pages/
│   │   ├── 1_overview.py       # Overall ESG summary
│   │   ├── 2_environmental.py
│   │   ├── 3_social.py
│   │   ├── 4_governance.py
│   │   └── 5_scoring.py
│   └── components/
│       ├── charts.py           # Reusable Plotly chart helpers
│       ├── kpi_cards.py        # KPI metric card components
│       └── sidebar.py          # Shared sidebar / filters
├── data/
│   ├── sample/                 # Sample CSVs for testing ingestion
│   └── uploads/                # Runtime upload target (gitignored)
├── database/
│   ├── schema.sql              # Table definitions
│   └── seed.sql                # Demo seed data
├── tests/
│   ├── test_ingestion.py
│   ├── test_scoring.py
│   └── test_analytics.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Setup

### 1. Clone and create the virtual environment

```bash
git clone <your-repo-url>
cd ESG
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
DEBUG=True
DATABASE_URL=postgresql://esg_user:esg_password@localhost:5432/esg_db
ENVIRONMENTAL_WEIGHT=0.40
SOCIAL_WEIGHT=0.30
GOVERNANCE_WEIGHT=0.30
```

### 4. Start PostgreSQL with Docker

```bash
docker-compose up -d db
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### 7. Start the Streamlit dashboard

```bash
streamlit run dashboard/main.py
```

Dashboard available at `http://localhost:8501`

---

## ESG scoring model

Scores are computed on a 0–100 scale using configurable weights:

| Pillar | Default weight | KPIs tracked |
|---|---|---|
| Environmental | 40% | CO₂ emissions, energy intensity, water consumption, waste |
| Social | 30% | Gender diversity ratio, employee retention, engagement score |
| Governance | 30% | Compliance score, risk index, audit success rate |

**Rating thresholds:**

| Score | Rating |
|---|---|
| ≥ 80 | A — Excellent |
| 60–79 | B — Good |
| 40–59 | C — Average |
| < 40 | D — Needs improvement |

Weights are configurable in `.env` and validated at startup to ensure they sum to 1.0.

---

## API endpoints (Phase 1)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/upload/csv` | Upload a CSV data file |
| `POST` | `/api/v1/upload/excel` | Upload an Excel data file |
| `GET` | `/api/v1/environmental/kpis` | Fetch environmental KPIs |
| `GET` | `/api/v1/social/kpis` | Fetch social KPIs |
| `GET` | `/api/v1/governance/kpis` | Fetch governance KPIs |
| `GET` | `/api/v1/scoring/overall` | Get overall ESG score + breakdown |
| `GET` | `/api/v1/scoring/history` | Score history over time |

---

## Running tests

```bash
pytest tests/ -v
```

---

## Docker deployment

Build and run the full stack (API + dashboard + database):

```bash
docker-compose up --build
```

---

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| Phase 1 | Foundation MVP — data pipeline, ESG modules, Streamlit dashboard | ✅ In progress |
| Phase 2 | Analytics & intelligence — predictive models, AI recommendations, React dashboard | Planned |
| Phase 3 | GenAI platform — ESG Copilot, RAG assistant, multi-agent advisory | Planned |

---

## Data sources

Sample datasets used for development and testing:

- [World Bank Open Data](https://data.worldbank.org)
- [UN Sustainable Development Goals](https://sdgs.un.org/goals)
- [CDP Open Data](https://www.cdp.net/en/guidance/guidance-for-companies)
- [Kaggle ESG Datasets](https://www.kaggle.com/search?q=ESG+sustainability)