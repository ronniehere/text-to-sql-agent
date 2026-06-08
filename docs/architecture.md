# Agentic architecture

This document describes the multi-node LangGraph runtime that powers Text-to-SQL Agent: grounded schema discovery, SQL synthesis, critique, and tool execution in a closed loop.

## System context

```mermaid
flowchart TB
    subgraph Client["Presentation layer"]
        UI["Streamlit conversational UI"]
        Browse["Schema / table browser"]
    end

    subgraph ControlPlane["Control plane"]
        API["FastAPI gateway"]
        Session["Session binder"]
        Redis[("Redis session store<br/>db_uri ↔ session_id")]
    end

    subgraph AgentRuntime["Agentic runtime"]
        Orchestrator["LangGraph StateGraph"]
        LLM["Vertex AI Gemini<br/>tool-calling planner"]
        Toolkit["SQLDatabaseToolkit"]
    end

    subgraph DataPlane["Data plane"]
        DB[("Target RDBMS<br/>PostgreSQL / SQLAlchemy URI")]
    end

    UI --> API
    Browse --> API
    API --> Session
    Session --> Redis
    API --> Orchestrator
    Orchestrator --> LLM
    Orchestrator --> Toolkit
    Toolkit --> DB
    LLM -.->|tool_calls| Toolkit
```

## Cognitive loop

Each natural-language question compiles into a **stateful agent graph**. Messages accumulate in `MessagesState`; the model never sees a raw URI — only tool results and dialect-aware prompts.

```mermaid
stateDiagram-v2
    [*] --> Discovery: START

    state Discovery {
        [*] --> ListTables
        ListTables --> SchemaPlanner: tables known
        SchemaPlanner --> SchemaTool: bind sql_db_schema
        SchemaTool --> [*]
    }

    Discovery --> Synthesis: schema grounded

    state Synthesis {
        [*] --> GenerateSQL
        GenerateSQL --> Decide: LLM turn
        Decide --> Critique: has tool_calls
        Decide --> [*]: final answer
        Critique --> Execute: validated SQL
        Execute --> GenerateSQL: observe rows / errors
    }

    Synthesis --> [*]: END
```

## Node responsibilities

| Node | Kind | Responsibility |
|------|------|----------------|
| `list_tables` | Tool bootstrap | Enumerate relations via `sql_db_list_tables` |
| `call_get_schema` | LLM + tools | Choose which tables need `sql_db_schema` |
| `get_schema` | ToolNode | Materialize DDL / column metadata into state |
| `generate_query` | LLM + tools | Intent → dialect-correct SQL (or natural-language answer) |
| `check_query` | LLM critic | Second-pass review for NULL/`UNION`/cast/join mistakes |
| `run_query` | ToolNode | Execute via `sql_db_query`, feed observations back |

## Control flow (compiled graph)

```mermaid
flowchart LR
    START([START]) --> LT[list_tables]
    LT --> CGS[call_get_schema]
    CGS --> GS[get_schema]
    GS --> GQ[generate_query]

    GQ -->|tool_calls present| CQ[check_query]
    GQ -->|no tool_calls| ENDN([END])

    CQ --> RQ[run_query]
    RQ -->|observation| GQ
```

The **generate → check → run → generate** cycle is the agentic heart of the system: the model can revise SQL after seeing execution feedback instead of failing on the first draft.

## Tool surface

```mermaid
flowchart LR
    subgraph BoundTools["Session-scoped toolkit"]
        T1["sql_db_list_tables"]
        T2["sql_db_schema"]
        T3["sql_db_query"]
        T4["sql_db_query_checker"]
    end

    Agent["LangGraph agent"] --> T1
    Agent --> T2
    Agent --> T3
    Agent --> T4
    T1 --> Engine["SQLAlchemy engine"]
    T2 --> Engine
    T3 --> Engine
    T4 --> Agent
```

Tools are **rebound per `session_id`**: Redis resolves the URI, `SQLDatabaseToolkit` builds a fresh toolset, and ToolNodes wrap schema/query execution for the graph.

## Request lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit
    participant API as FastAPI
    participant Redis
    participant Graph as LangGraph
    participant Gemini as Vertex AI
    participant DB as Database

    User->>UI: Connect with DB URI
    UI->>API: POST /api/connect-db
    API->>DB: SELECT 1 health check
    API->>Redis: SET db_uri:session TTL 24h

    User->>UI: Natural language question
    UI->>API: POST /api/query
    API->>Redis: GET db_uri:session
    API->>Graph: invoke MessagesState

    Graph->>DB: list tables / schema tools
    Graph->>Gemini: plan + synthesize SQL
    Gemini-->>Graph: tool_calls query
    Graph->>Gemini: critique pass
    Graph->>DB: execute SQL
    DB-->>Graph: rows / error observation
    Graph->>Gemini: finalize answer
    Graph-->>API: last message content
    API-->>UI: { answer }
    UI-->>User: Rendered reply
```

## Design properties

- **Grounded generation** — SQL is produced only after table listing and schema fetch, reducing hallucination of columns.
- **Critic-before-execute** — a dedicated check node reviews SQL before the run tool fires.
- **Observation loop** — failed or partial runs return into `generate_query` for another planner turn.
- **Session isolation** — each browser session owns its own URI binding; the graph is compiled per request against that binding.
- **Dialect awareness** — prompts inject `db.dialect` so Postgres vs other engines stay consistent.
