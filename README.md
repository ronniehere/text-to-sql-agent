# Text-to-SQL Agent

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-agentic-1C3C3C)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-gateway-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vertex AI](https://img.shields.io/badge/Vertex%20AI-Gemini-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/vertex-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Agentic text-to-SQL runtime** — a multi-node LangGraph system that discovers schema, synthesizes SQL, critiques it, executes tools, and loops on observations until it can answer in natural language.

Ask a relational database questions in plain language. The agent inspects schema, writes SQL, runs it, and returns an answer — no hand-written queries required.

Built for **demos, internal tools, and prototyping** where analysts or operators need quick answers from PostgreSQL (or other SQLAlchemy-supported databases) without living in a SQL console.

<p align="center">
  <img src="docs/assets/demo.gif" alt="Text-to-SQL Agent demo: connect a database, browse tables, ask a question, get an answer" width="900" />
</p>

**Demo flow:** connect sample Postgres → browse `employees` → ask in plain English → agent grounds on schema, writes SQL, critiques, executes, answers.

## Problem

Most business data already lives in SQL databases, but asking for it usually means:

- Knowing the schema and dialect
- Writing and debugging queries by hand
- Waiting on someone who can

This project bridges that gap: connect a database URI, browse tables, and chat in natural language. A LangGraph agent uses Vertex AI (Gemini) plus SQL tools to generate, review, and execute queries on your behalf.

## Agentic system overview

The stack is split into a **presentation layer**, a **control plane** (API + session memory), and an **agentic runtime** that orchestrates LLM reasoning with SQL tools.

```mermaid
flowchart TB
    subgraph Present["Presentation"]
        UI["Streamlit chat + table browser"]
    end

    subgraph Control["Control plane"]
        API["FastAPI gateway"]
        Redis[("Redis<br/>session → DB URI")]
    end

    subgraph Runtime["Agentic runtime"]
        Graph["LangGraph StateGraph"]
        Planner["Planner / synthesizer<br/>Vertex AI Gemini"]
        Critic["SQL critic node"]
        Tools["SQLDatabaseToolkit<br/>list · schema · query"]
    end

    subgraph Data["Data plane"]
        DB[("Your RDBMS")]
    end

    UI -->|REST| API
    API --> Redis
    API --> Graph
    Graph --> Planner
    Graph --> Critic
    Graph --> Tools
    Tools --> DB
    Planner -.->|tool_calls| Tools
    Critic -.->|validated SQL| Tools
```

### Cognitive loop (why it feels “agentic”)

Unlike a single prompt → SQL call, every question walks a **compiled graph** with grounding, critique, and an observation loop:

```mermaid
flowchart LR
    START([START]) --> Discover["① Discover<br/>list_tables"]
    Discover --> Ground["② Ground<br/>schema tools"]
    Ground --> Synthesize["③ Synthesize<br/>generate_query"]
    Synthesize -->|tool_calls| Critique["④ Critique<br/>check_query"]
    Synthesize -->|final text| DONE([END])
    Critique --> Execute["⑤ Execute<br/>run_query"]
    Execute -->|rows / errors| Synthesize
```

| Phase | Graph node(s) | What the agent does |
|-------|----------------|---------------------|
| Discover | `list_tables` | Enumerate relations so the model cannot invent table names |
| Ground | `call_get_schema` → `get_schema` | Pull column/DDL context via tools |
| Synthesize | `generate_query` | Intent → dialect-aware SQL (or a final NL answer) |
| Critique | `check_query` | Second LLM pass for NULL / join / cast mistakes |
| Execute | `run_query` | Run SQL; feed observations back into synthesis |

Full write-up with sequence diagrams and tool surface: **[docs/architecture.md](docs/architecture.md)**.

### End-to-end request path

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant UI as Streamlit
    participant API as FastAPI
    participant R as Redis
    participant G as LangGraph
    participant L as Gemini
    participant DB as Database

    U->>UI: Ask in natural language
    UI->>API: POST /api/query
    API->>R: Resolve session DB URI
    API->>G: invoke agent
    G->>DB: list tables + schema
    G->>L: plan SQL
    L-->>G: tool_calls
    G->>L: critique SQL
    G->>DB: execute
    DB-->>G: observation
    G->>L: finalize answer
    G-->>UI: answer
```

## What you get

| Layer | Role |
|-------|------|
| **Streamlit UI** | Connect DB, preview tables, chat with results |
| **FastAPI** | Session lifecycle + `/api/query` |
| **LangGraph agent** | Multi-node loop: discover → ground → synthesize → critique → execute |
| **Redis** | Maps `session_id` → database URI (24h TTL) |
| **Vertex AI** | Gemini model for planning, synthesis, and SQL critique |
| **SQL toolkit** | Session-scoped `list_tables` / `schema` / `query` tools |

## Repository layout

```
text-to-sql-agent/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + CORS
│   │   ├── api/routes.py     # REST endpoints
│   │   ├── agent/            # LangGraph graph, tools, LLM
│   │   └── config/settings.py
│   ├── db/hr_db.sql          # Sample PostgreSQL HR schema
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py                # Streamlit chat + table browser
│   ├── assets/               # Chat avatars
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements.txt
├── docs/
│   └── architecture.md       # Agentic graph, tools, sequences
├── docker-compose.yml        # Redis + API + UI
├── LICENSE
└── README.md
```

## Prerequisites

| Need | Why |
|------|-----|
| Python 3.11+ | Backend + Streamlit |
| Docker Desktop (recommended) | Redis, Postgres sample DB, one-command stack |
| Google Cloud project + Vertex AI | Gemini powers the agent |
| Service account JSON | ADC for Vertex (`backend/app/config/key.json`) |

## How to run

### 1. Clone

```bash
git clone https://github.com/ronniehere/text-to-sql-agent.git
cd text-to-sql-agent
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` (required fields):

| Variable | Purpose | Example |
|----------|---------|---------|
| `GCP_PROJECT_ID` | Your GCP project | `my-gcp-project` |
| `GCP_REGION` | Vertex region | `us-central1` |
| `VERTEX_AI_MODEL` | Chat model | `gemini-2.0-flash` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to key inside backend | `app/config/key.json` |
| `REDIS_HOST` / `REDIS_PORT` | Session store | `localhost` / `6379` (Compose overrides host to `redis`) |
| `CORS_ORIGINS` | Allowed UI origins | `http://localhost:8501` |

1. Download a GCP service account key with **Vertex AI User** (or broader Vertex access).
2. Save it as `backend/app/config/key.json` (this path is gitignored).

`frontend/.env`:

```env
BACKEND_API_URL=http://localhost:8000
```

### 3. Start the stack (easiest)

Compose brings up **Redis**, a **sample Postgres** (`hr_demo` with `employees`), the **API**, and the **UI**:

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| UI | http://localhost:8501 |
| API docs | http://localhost:8000/docs |
| Sample Postgres | `localhost:5432` |

Sample DB (Compose):

| Where you connect from | URI to use |
|------------------------|------------|
| **UI / API while app runs in Compose** | `postgresql://demo:demo@postgres:5432/hr_demo` |
| Host tools (`psql`, GUI) | `postgresql://demo:demo@localhost:5432/hr_demo` |

Use the hostname `postgres` in the UI when the backend container talks to the DB (Compose DNS). Use `localhost` only if the backend process runs on your machine.

Stop with `Ctrl+C`, or `docker compose down`. Reset the sample DB with `docker compose down -v` if you need a clean seed.

### 4. Run without Docker (manual)

You still need Redis and a database somewhere.

```bash
# Terminal A — Redis (example)
docker run --name ttsql-redis -p 6379:6379 -d redis:7-alpine

# Terminal B — Backend
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal C — Frontend
cd frontend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501.

## How to test with a database

### Option A — Use the bundled sample (recommended)

1. Start Compose (`docker compose up --build`) so Postgres is seeded from `backend/db/hr_db.sql`.
2. Open http://localhost:8501.
3. In **Schema atelier**, paste the URI that matches how you started the backend:

   ```text
   # Backend in Docker Compose (recommended for this guide):
   postgresql://demo:demo@postgres:5432/hr_demo

   # Backend running on your machine (manual install):
   postgresql://demo:demo@localhost:5432/hr_demo
   ```

4. Click **Connect database**. Status should flip to **Connected**.
5. Browse the `employees` table on the left (preview rows).
6. In **Conversation**, try questions such as:

   | Try asking… | What you should see |
   |-------------|---------------------|
   | `How many employees are in Engineering?` | A count (sample has several engineers) |
   | `Who are the highest paid employees?` | Names + salaries, limited rows |
   | `List people hired after 2022` | Filtered by `hire_date` |
   | `Average salary by department` | Aggregated numbers |
   | `Show active HR staff` | Rows with department/status filters |

7. Confirm the spinner text runs the agent loop, then an answer appears in chat.

**What’s in the sample DB?** One table, `employees` (id, name, department, hire_date, salary, email, job_title, status, phone, manager_id) with ~17 demo rows across Engineering, HR, Marketing, Finance, Sales.

### Option B — Seed Postgres yourself

If you already run PostgreSQL:

```bash
createdb hr_demo   # or: psql -c "CREATE DATABASE hr_demo;"
psql -d hr_demo -f backend/db/hr_db.sql
```

Connect from the UI with your real URI, for example:

```text
postgresql://postgres:YOUR_PASSWORD@localhost:5432/hr_demo
```

### Option C — Point at your own database

Any SQLAlchemy-compatible URI works (PostgreSQL is the best-tested path):

```text
postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

Tips:

- Prefer a **read-only** DB user for safety.
- Start with a small schema so schema-tool calls stay fast.
- If connect fails, check host/port from the machine running the **browser** and the **backend** (Compose maps Postgres to `localhost:5432` on your host).

### Option D — Hit the API with curl (no UI)

```bash
SESSION=$(python -c "import uuid; print(uuid.uuid4().hex)")

# 1) Bind a database to the session
# Use @postgres if the API container is in Compose; @localhost if API is on the host
curl -s -X POST http://localhost:8000/api/connect-db \
  -H "Content-Type: application/json" \
  -d "{\"db_uri\":\"postgresql://demo:demo@postgres:5432/hr_demo\",\"session_id\":\"$SESSION\"}"

# 2) List tables
curl -s -X POST http://localhost:8000/api/db-tables \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\"}"

# 3) Ask a natural-language question
curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION\",\"query\":\"How many employees work in Engineering?\"}"
```

Windows PowerShell equivalent for a quick query test (after connect):

```powershell
$session = [guid]::NewGuid().ToString("N")
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/connect-db -ContentType "application/json" -Body (@{ db_uri = "postgresql://demo:demo@postgres:5432/hr_demo"; session_id = $session } | ConvertTo-Json)
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/query -ContentType "application/json" -Body (@{ session_id = $session; query = "How many employees work in Engineering?" } | ConvertTo-Json)
```

### Troubleshooting

| Symptom | What to check |
|---------|----------------|
| UI toast: could not reach API | Backend on `:8000`, `BACKEND_API_URL=http://localhost:8000` |
| Connect failed | URI/password, Postgres up (`docker compose ps`). With Compose UI use host `postgres`, not `localhost`. Vertex not required for connect |
| Query fails / 400 from agent | `key.json` present, `GCP_PROJECT_ID` set, Vertex AI API enabled in GCP |
| Redis errors in backend logs | Redis container healthy; for manual run, `REDIS_HOST=localhost` |
| Empty tables | Wrong database name, or seed didn’t run — `docker compose down -v && docker compose up --build` |

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/connect-db` | Validate URI, bind to `session_id` |
| `POST` | `/api/disconnect-db` | Clear session binding |
| `POST` | `/api/db-tables` | List tables |
| `POST` | `/api/db-table` | Preview rows for one table |
| `POST` | `/api/query` | Natural-language question → agent answer |

`POST /api/query` body:

```json
{ "session_id": "...", "query": "Who are the highest paid engineers?" }
```

Response:

```json
{ "answer": "..." }
```

## Security notes

- Database credentials are entered in the UI and stored in Redis for the session — treat this as a **trusted environment / demo** tool, not a public multi-tenant SaaS.
- The agent prompt discourages destructive SQL, but the toolkit can still execute whatever SQL the model produces. Prefer a **read-only DB user** in production-like setups.
- **Never commit secrets:** keep `backend/.env`, `frontend/.env`, and `backend/app/config/key.json` local only (gitignored). Only `*.env.example` files belong in git, with placeholders like `your-gcp-project-id`.
- Compose sample login `demo` / `demo` is a **local throwaway** Postgres user for the bundled HR seed — not a cloud API key. Change it if you expose the port beyond your machine.

## License

MIT — see [LICENSE](LICENSE).
