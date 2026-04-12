from dotenv import load_dotenv
from pathlib import Path
import html
import os
import re
import uuid

import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).parent
load_dotenv(dotenv_path=ROOT / ".env")
API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Text-to-SQL Agent",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- styles -----------------------------------------------------------------
css_path = ROOT / "assets" / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# --- session state ----------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db_session_id" not in st.session_state:
    st.session_state.db_session_id = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = False
if "table_names" not in st.session_state:
    st.session_state.table_names = []


def add_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})


def contains_arabic(text: str) -> bool:
    return bool(
        re.search(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]",
            text,
        )
    )


def connect_db(db_uri: str) -> None:
    session_id = uuid.uuid4().hex
    try:
        res = requests.post(
            f"{API_URL}/api/connect-db",
            json={"db_uri": db_uri, "session_id": session_id},
            timeout=30,
        )
        response = res.json()
        if "message" in response:
            st.session_state.db_session_id = session_id
            st.session_state.messages = []
            st.toast("Database connected")
            st.rerun()
        else:
            st.toast(response.get("detail", "Connection failed"))
    except Exception:
        st.toast("Could not reach the API. Is the backend running?")


def disconnect_db() -> None:
    try:
        res = requests.post(
            f"{API_URL}/api/disconnect-db",
            json={"session_id": st.session_state.db_session_id},
            timeout=15,
        )
        response = res.json()
        if "message" in response:
            st.session_state.db_session_id = None
            st.session_state.messages = []
            st.session_state.table_names = []
            st.toast("Disconnected")
            st.rerun()
        else:
            st.toast(response.get("detail", "Disconnect failed"))
    except Exception:
        st.toast("Could not reach the API.")


def load_tables() -> list[str]:
    try:
        res = requests.post(
            f"{API_URL}/api/db-tables",
            json={"session_id": st.session_state.db_session_id},
            timeout=30,
        )
        response = res.json()
        return response.get("tables", [])
    except Exception:
        return []


def fetch_table(table_name: str) -> pd.DataFrame | None:
    try:
        res = requests.post(
            f"{API_URL}/api/db-table",
            json={
                "session_id": st.session_state.db_session_id,
                "table_name": table_name,
            },
            timeout=60,
        )
        response = res.json()
        if "data" in response:
            return pd.DataFrame(response["data"])
    except Exception:
        return None
    return None


def run_agent_query(question: str) -> str:
    try:
        res = requests.post(
            f"{API_URL}/api/query",
            json={
                "session_id": st.session_state.db_session_id,
                "query": question,
            },
            timeout=180,
        )
        response = res.json()
        if "answer" in response:
            return response["answer"]
        return response.get("detail", "Error: No result returned.")
    except Exception:
        return "Something went wrong while querying."


# --- header -----------------------------------------------------------------
connected = st.session_state.db_session_id is not None
status_class = "is-live" if connected else "is-idle"
status_label = "Connected" if connected else "No database"

st.markdown(
    f"""
    <div class="ttsql-header">
      <div>
        <p class="ttsql-brand">Text-to-SQL</p>
        <p class="ttsql-tag">Ask your database in plain language. The agent grounds on schema, writes SQL, critiques it, then answers.</p>
      </div>
      <div class="ttsql-status {status_class}">{status_label}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

schema_col, chat_col = st.columns([0.95, 1.25], gap="large")

# --- schema rail ------------------------------------------------------------
with schema_col:
    st.markdown('<p class="ttsql-panel-label">Schema atelier</p>', unsafe_allow_html=True)

    if not connected:
        st.markdown(
            """
            <div class="ttsql-empty">
              <h2>Wire up a database</h2>
              <p>Paste a SQLAlchemy URI. PostgreSQL works best. The agent only sees schema through tools — never invents tables out of thin air.</p>
              <div class="ttsql-chip-row">
                <span class="ttsql-chip">discover → ground</span>
                <span class="ttsql-chip">synthesize → critique</span>
                <span class="ttsql-chip">execute → answer</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        db_uri = st.text_input(
            "Database URI",
            placeholder="postgresql://demo:demo@postgres:5432/hr_demo",
            label_visibility="collapsed",
            key="db_uri_input",
        )
        if st.button("Connect database", use_container_width=True, type="primary"):
            if db_uri.strip():
                connect_db(db_uri.strip())
            else:
                st.toast("Enter a database URI first")
    else:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.caption(f"Session `{st.session_state.db_session_id[:8]}…`")
        with c2:
            if st.button("Disconnect", use_container_width=True):
                disconnect_db()

        if not st.session_state.pending_query:
            tables = load_tables()
            st.session_state.table_names = tables
            if tables:
                table = st.selectbox("Browse table", tables, label_visibility="visible")
                frame = fetch_table(table)
                if frame is not None:
                    st.caption(f"{len(frame)} rows · preview")
                    st.dataframe(frame, use_container_width=True, height=420)
            else:
                st.warning("No tables found in this database.")

# --- conversation -----------------------------------------------------------
with chat_col:
    st.markdown('<p class="ttsql-panel-label">Conversation</p>', unsafe_allow_html=True)

    if not connected:
        st.markdown(
            """
            <div class="ttsql-empty">
              <h2>Conversation waits on a connection</h2>
              <p>Once a database is linked, ask things like department headcount, top salaries, or hire-date ranges — in everyday language.</p>
              <div class="ttsql-chip-row">
                <span class="ttsql-chip">Who joined after 2022?</span>
                <span class="ttsql-chip">Avg salary by department</span>
                <span class="ttsql-chip">List active engineers</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        if not st.session_state.messages:
            st.markdown(
                """
                <div class="ttsql-empty">
                  <h2>Ask anything about the data</h2>
                  <p>The agent will list tables, pull schema, draft SQL, review it, run it, and reply with the result.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        for message in st.session_state.messages:
            role = "user" if message["role"] == "user" else "assistant"
            with st.chat_message(role):
                direction = "rtl" if contains_arabic(message["content"]) else "ltr"
                safe = html.escape(message["content"]).replace("\n", "<br>")
                st.markdown(
                    f'<div dir="{direction}">{safe}</div>',
                    unsafe_allow_html=True,
                )

        if query := st.chat_input(
            "Ask about your data…",
            disabled=st.session_state.pending_query,
        ):
            add_message("user", query)
            st.session_state.pending_query = True
            st.rerun()

        if (
            st.session_state.messages
            and st.session_state.messages[-1]["role"] == "user"
            and st.session_state.pending_query
        ):
            with st.spinner("Agent looping: schema → SQL → critique → execute…"):
                answer = run_agent_query(st.session_state.messages[-1]["content"])
                add_message("ai", answer)
                st.session_state.pending_query = False
                st.rerun()
