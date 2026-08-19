"""
Text-to-SQL — Streamlit Application
=====================================
Convert natural language to SQL using open-source LLMs via Groq API.
Supports a built-in SQLite test database and custom MySQL connections.
"""

import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Local imports
from core.text_to_sql import TextToSQL
from core.llm_client import GROQ_MODELS
from db.connector import get_sqlite_engine, get_mysql_engine
from db.schema_extractor import extract_schema, get_table_names, get_sample_rows
from db.query_executor import execute_query, QueryExecutionError
from data.init_db import init_test_database, get_db_path

load_dotenv()

# DEMO_MODE powers the public CV/portfolio deployment: it hides the
# "connect to any MySQL server" form (so strangers can't use the hosted
# app to reach arbitrary hosts) and never puts the shared Groq key into
# a widget's value (Streamlit sends default widget values to the client
# even for password fields, which would leak it).
DEMO_MODE = os.getenv("APP_DEMO_MODE", "false").strip().lower() in ("1", "true", "yes")
SHARED_API_KEY = os.getenv("GROQ_API_KEY", "")

# ──────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Text → SQL",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* Main header */
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-top: 0.2rem;
        margin-bottom: 2rem;
    }
    /* SQL code box */
    .sql-box {
        background: #1e1e2e;
        border: 1px solid #3d3d5c;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        color: #cdd6f4;
        white-space: pre-wrap;
        word-break: break-word;
        line-height: 1.6;
    }
    /* Status badges */
    .badge-success { color: #22c55e; font-weight: 600; }
    .badge-error   { color: #ef4444; font-weight: 600; }
    /* Schema card */
    .schema-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-family: monospace;
        font-size: 0.8rem;
        color: #334155;
        max-height: 350px;
        overflow-y: auto;
    }
    /* Example chips */
    .example-label {
        font-size: 0.82rem;
        color: #6b7280;
        margin-bottom: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Session state defaults
# ──────────────────────────────────────────────
if "engine"  not in st.session_state: st.session_state.engine  = None
if "schema"  not in st.session_state: st.session_state.schema  = None
if "dialect" not in st.session_state: st.session_state.dialect = "SQLite"
if "history" not in st.session_state: st.session_state.history = []  # list of {question, sql, df}


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # ── LLM ──────────────────────────────────
    st.markdown("### 🤖 LLM (Groq)")
    if DEMO_MODE:
        user_api_key = st.text_input(
            "Groq API Key (optional)",
            type="password",
            value="",
            help="This demo works out of the box with a shared key. "
                 "Paste your own free key at https://console.groq.com to use your own quota instead.",
            placeholder="Leave blank to use the demo key",
        )
        api_key = user_api_key or SHARED_API_KEY
    else:
        api_key = st.text_input(
            "Groq API Key",
            type="password",
            value=SHARED_API_KEY,
            help="Get your free key at https://console.groq.com",
            placeholder="gsk_...",
        )
    model = st.selectbox("Model", GROQ_MODELS, index=0)

    st.caption("💡 [Get a free Groq API key](https://console.groq.com)")

    st.divider()

    # ── Database ─────────────────────────────
    st.markdown("### 🗄️ Database")

    if DEMO_MODE:
        db_mode = "🧪 Test Database (SQLite)"
        st.caption("🌐 Public demo — sample e-commerce data only. Run locally to connect your own MySQL database.")
    else:
        db_mode = st.radio(
            "Connection type",
            ["🧪 Test Database (SQLite)", "🐬 MySQL (Custom)"],
            index=0,
        )

    if "Test" in db_mode:
        # Auto-connect to the bundled SQLite test DB
        if st.button("🔌 Connect to Test DB", use_container_width=True):
            with st.spinner("Initializing test database…"):
                db_path = init_test_database()
                engine  = get_sqlite_engine(db_path)
                st.session_state.engine  = engine
                st.session_state.schema  = extract_schema(engine)
                st.session_state.dialect = "SQLite"
            st.success("✅ Connected to test database!")

    else:
        # MySQL form
        with st.form("mysql_form"):
            host     = st.text_input("Host",     "localhost")
            port     = st.number_input("Port",   value=3306, step=1)
            database = st.text_input("Database", "")
            username = st.text_input("Username", "")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔌 Connect", use_container_width=True)

        if submitted:
            with st.spinner("Connecting to MySQL…"):
                try:
                    engine = get_mysql_engine(
                        host=host, port=int(port), database=database,
                        username=username, password=password,
                    )
                    st.session_state.engine  = engine
                    st.session_state.schema  = extract_schema(engine)
                    st.session_state.dialect = "MySQL"
                    st.success(f"✅ Connected to `{database}`!")
                except Exception as e:
                    st.error(f"❌ Connection failed: {e}")

    # ── Schema preview ────────────────────────
    if st.session_state.schema:
        st.divider()
        st.markdown("### 📋 Schema")
        st.markdown(
            f'<div class="schema-card">{st.session_state.schema}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### 🗑️ History")
    if st.button("Clear history", use_container_width=True):
        st.session_state.history = []
        st.rerun()


# ──────────────────────────────────────────────
# Main content
# ──────────────────────────────────────────────
st.markdown('<p class="main-title">🔍 Text → SQL</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Ask a question in plain English — get a SQL query instantly.</p>',
    unsafe_allow_html=True,
)

# ── Connection guard ──────────────────────────
if not st.session_state.engine:
    st.info(
        "👈 **Connect to a database first** using the sidebar.\n\n"
        "Try the **🧪 Test Database** to explore the demo e-commerce schema right away!"
    )
    st.stop()

tab_query, tab_preview = st.tabs(["💬 Ask a question", "🔎 Data preview"])

with tab_query:
    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar.")
    else:
        # ── Example questions ─────────────────────────
        EXAMPLES = [
            "Show me the top 5 customers by total spending",
            "How many orders were delivered last year?",
            "Which products are out of stock?",
            "List all orders with their customer name and status",
            "What is the average order value per country?",
            "Show the 3 best-selling products by quantity sold",
            "Which customers have never placed an order?",
            "What is the monthly revenue breakdown?",
        ]

        st.markdown('<p class="example-label">💡 Try an example:</p>', unsafe_allow_html=True)
        cols = st.columns(4)
        clicked_example = None
        for i, ex in enumerate(EXAMPLES):
            if cols[i % 4].button(ex, key=f"ex_{i}", use_container_width=True):
                clicked_example = ex

        # ── Question input ────────────────────────────
        st.markdown("#### Ask your question")
        question = st.text_area(
            "Natural language question",
            value=clicked_example or "",
            placeholder="e.g. Show me all customers from France who placed more than 2 orders",
            height=90,
            label_visibility="collapsed",
        )

        generate_col, _ = st.columns([1, 4])
        generate_btn = generate_col.button("⚡ Generate SQL", type="primary", use_container_width=True)

        # ── Generate ──────────────────────────────────
        if generate_btn and question.strip():
            converter = TextToSQL(api_key=api_key, model=model)

            with st.spinner("Generating SQL…"):
                result = converter.convert(
                    question=question,
                    schema=st.session_state.schema,
                    dialect=st.session_state.dialect,
                )

            if result["error"]:
                st.error(f"❌ {result['error']}")
                if result["raw"]:
                    with st.expander("Raw LLM output"):
                        st.code(result["raw"])
            else:
                sql = result["formatted"]

                st.markdown("#### 📝 Generated SQL")
                st.markdown(f'<div class="sql-box">{sql}</div>', unsafe_allow_html=True)

                # Copy-friendly code block
                with st.expander("📋 Copy-ready SQL"):
                    st.code(result["sql"], language="sql")

                # ── Execute ───────────────────────────
                st.markdown("#### ▶️ Execute & Results")
                exec_col, _ = st.columns([1, 5])
                if exec_col.button("▶ Run Query", use_container_width=True):
                    with st.spinner("Running query…"):
                        try:
                            df = execute_query(st.session_state.engine, result["sql"])
                            if df.empty:
                                st.info("✅ Query ran successfully but returned no rows.")
                            else:
                                st.success(f"✅ {len(df)} row(s) returned")
                                st.dataframe(df, use_container_width=True, hide_index=True)
                                # Save to history
                                st.session_state.history.append({
                                    "question": question,
                                    "sql": result["sql"],
                                    "rows": len(df),
                                })
                        except QueryExecutionError as e:
                            st.error(f"❌ Query error: {e}")
                else:
                    # Auto-execute if user clicks Generate
                    with st.spinner("Running query…"):
                        try:
                            df = execute_query(st.session_state.engine, result["sql"])
                            if df.empty:
                                st.info("✅ Query ran successfully but returned no rows.")
                            else:
                                st.success(f"✅ {len(df)} row(s) returned")
                                st.dataframe(df, use_container_width=True, hide_index=True)
                                st.session_state.history.append({
                                    "question": question,
                                    "sql": result["sql"],
                                    "rows": len(df),
                                })
                        except QueryExecutionError as e:
                            st.error(f"❌ Query error: {e}")

        elif generate_btn and not question.strip():
            st.warning("Please enter a question first.")

with tab_preview:
    st.markdown("#### 🔎 Data preview")
    st.caption("A quick look at the rows in each table of the connected database.")

    tables = get_table_names(st.session_state.engine)
    if not tables:
        st.info("No tables found in this database.")
    else:
        preview_col, rows_col = st.columns([3, 1])
        selected_table = preview_col.selectbox("Table", tables, key="preview_table")
        n_rows = rows_col.number_input("Rows", min_value=1, max_value=100, value=10, step=5)

        try:
            sample = get_sample_rows(st.session_state.engine, selected_table, limit=int(n_rows))
            if sample:
                st.dataframe(pd.DataFrame(sample), use_container_width=True, hide_index=True)
            else:
                st.info("This table is empty.")
        except Exception as e:
            st.error(f"❌ Could not preview table `{selected_table}`: {e}")


# ──────────────────────────────────────────────
# History panel
# ──────────────────────────────────────────────
if st.session_state.history:
    st.divider()
    st.markdown("### 🕓 Query History")
    for i, item in enumerate(reversed(st.session_state.history[-10:])):
        with st.expander(f"**Q:** {item['question']}  — `{item['rows']} rows`"):
            st.code(item["sql"], language="sql")


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.divider()
st.caption(
    "Built with [Streamlit](https://streamlit.io) · "
    "LLM via [Groq](https://groq.com) · "
    "Open-source models: GPT-OSS, Qwen"
)
