# Contributing

Thanks for interest in improving Text-to-SQL Agent.

## Dev setup

1. Follow the [README](README.md) quick start (Redis + Vertex AI credentials required).
2. Prefer a read-only database user when testing the agent loop.
3. Keep secrets out of git (`.env`, `key.json`).

## Guidelines

- Match existing layout: `backend/app` for API/agent, `frontend` for Streamlit.
- Keep the agent graph readable; document non-obvious LangGraph edges in PRs.
- Avoid hardcoding deployment hostnames; use `CORS_ORIGINS` and env vars.
- Small, focused PRs are easier to review.

## Reporting issues

Include Python version, whether you used Docker Compose, and the API error body (redact credentials).
