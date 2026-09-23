import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time
import os
import platform
from pathlib import Path
from datetime import datetime
import duckdb
from google.genai.local_tokenizer import LocalTokenizer

# ----------------------------------------------------------------------
# Page Setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Local AI Engineering Studio",
    page_icon="⚡",
    layout="wide"
)

DB_PATH = os.path.join(os.path.dirname(__file__), "local_analytics.duckdb")
OLLAMA_BASE_URL = "http://localhost:11434"

# ----------------------------------------------------------------------
# Local Database Initialization (DuckDB)
# ----------------------------------------------------------------------
def init_db():
    with duckdb.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompt_logs (
                id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP,
                model VARCHAR,
                task VARCHAR,
                prompt VARCHAR,
                response VARCHAR,
                prompt_tokens INTEGER,
                response_tokens INTEGER,
                total_tokens INTEGER,
                duration_sec DOUBLE,
                tokens_per_sec DOUBLE
            );
            CREATE TABLE IF NOT EXISTS rag_documents (
                doc_id VARCHAR PRIMARY KEY,
                filename VARCHAR,
                chunk_index INTEGER,
                content VARCHAR,
                token_count INTEGER
            );
        """)

init_db()

# ----------------------------------------------------------------------
# Local Tokenizer & Helpers
# ----------------------------------------------------------------------
@st.cache_resource
def get_tokenizer(model_name: str = "gemini-2.5-pro"):
    return LocalTokenizer(model_name=model_name)

def fetch_ollama_models():
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=1.5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []

# ----------------------------------------------------------------------
# Navigation Header & Sidebar
# ----------------------------------------------------------------------
st.sidebar.title("⚙️ System Status")
st.sidebar.subheader("Available Local Models")
sidebar_models = fetch_ollama_models()
if sidebar_models:
    for m in sidebar_models:
        st.sidebar.markdown(f"📦 `{m}`")
else:
    st.sidebar.warning("No models found. Make sure Ollama is running.")

st.sidebar.divider()
os_choice = st.sidebar.radio(
    "Select your Operating System:",
    ["Windows", "Linux", "iOS / macOS"]
)

actual_os = platform.system()
is_valid_os = False

if os_choice == "Windows" and actual_os == "Windows":
    is_valid_os = True
elif os_choice == "Linux" and actual_os == "Linux":
    is_valid_os = True
elif os_choice == "iOS / macOS" and actual_os == "Darwin":
    is_valid_os = True

if not is_valid_os:
    st.error(f"❌ **Error:** You selected **{os_choice}**, but you are actually running on **{actual_os}**! Please select the correct Operating System to proceed.")
    st.stop()
else:
    st.sidebar.success(f"Verified **{os_choice}** environment.")

st.title("⚡ Local AI Engineering Studio")
st.caption("100% Private, Offline & Free. Runs directly on your machine with Ollama, DuckDB, SentencePiece & Streamlit.")

tabs = st.tabs([
    "🤖 1. Local Model Inference",
    "📚 2. Local Document Search / RAG",
    "🔍 3. Codebase Token Auditor",
    "⚖️ 4. Prompt Comparator & Eval",
    "📊 5. DuckDB Analytics & SQL"
])

# ======================================================================
# TAB 1: Local Model Inference (Ollama)
# ======================================================================
with tabs[0]:
    st.subheader("Run Real Open-Weights Models Locally")
    models = fetch_ollama_models()

    if not models:
        st.warning("Ollama daemon is not detected at `localhost:11434`. Start it with `ollama serve`.")
    else:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected_model = st.selectbox("Active Local Model:", models, index=0)
        with col2:
            temperature = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.05)
        with col3:
            tokenizer = get_tokenizer("gemini-2.5-pro")
            st.metric("Ollama Status", "Online 🟢")

        prompt_input = st.text_area(
            "User Prompt:",
            height=120,
            value="Write a Python function to compute the Fibonacci sequence using memoization.",
            placeholder="Enter your prompt here..."
        )

        col_run, col_tcount = st.columns([1, 4])
        with col_run:
            run_btn = st.button("🚀 Run Locally", type="primary", use_container_width=True)
        with col_tcount:
            if prompt_input:
                p_tokens = tokenizer.count_tokens(prompt_input).total_tokens
                st.caption(f"Input Tokens: **{p_tokens}** | Zero Cloud Call")

        if run_btn and prompt_input:
            response_placeholder = st.empty()
            full_response = ""
            start_time = time.time()

            with st.spinner(f"Generating on {selected_model}..."):
                try:
                    payload = {
                        "model": selected_model,
                        "prompt": prompt_input,
                        "stream": True,
                        "options": {"temperature": temperature}
                    }
                    res = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, stream=True)
                    
                    eval_count = 0
                    for line in res.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                full_response += chunk["response"]
                                response_placeholder.markdown(full_response + "▌")
                            if chunk.get("done"):
                                eval_count = chunk.get("eval_count", 0)

                    duration = time.time() - start_time
                    response_placeholder.markdown(full_response)

                    # Performance Metrics
                    tps = (eval_count / duration) if duration > 0 and eval_count > 0 else 0
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("Tokens Generated", f"{eval_count} tokens")
                    with m2:
                        st.metric("Inference Time", f"{duration:.2f} s")
                    with m3:
                        st.metric("Generation Speed", f"{tps:.1f} tokens/s")

                    # Log to DuckDB
                    with duckdb.connect(DB_PATH) as conn:
                        conn.execute("""
                            INSERT INTO prompt_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(time.time()),
                            datetime.now(),
                            selected_model,
                            "Interactive Inference",
                            prompt_input,
                            full_response,
                            p_tokens,
                            eval_count,
                            p_tokens + eval_count,
                            round(duration, 3),
                            round(tps, 2)
                        ))
                    st.toast("Result logged to DuckDB", icon="💾")

                except Exception as e:
                    st.error(f"Inference error: {e}")

# ======================================================================
# TAB 2: Local Document Search / RAG
# ======================================================================
with tabs[1]:
    st.subheader("Offline Document Indexing & Keyword / Semantic Search")
    st.write("Chunk and index private documents locally into DuckDB without uploading to any cloud.")

    col_docs, col_search = st.columns([1, 1])

    with col_docs:
        st.markdown("##### 📄 1. Index New Content")
        doc_name = st.text_input("Document Name / Title:", value="System Architecture Notes")
        doc_body = st.text_area(
            "Document Text to Index:",
            height=180,
            value="""Streamlit is an open-source Python framework that allows developers to create interactive web applications for data science and machine learning.

DuckDB is an in-process SQL OLAP database management system designed for fast analytical queries directly on local files, Parquet, and in-memory tables.

Ollama lets you run large language models such as Llama 3, Mistral, and Qwen locally on your machine with full GPU acceleration and privacy.

SentencePiece provides unsupervised text tokenization without cloud dependencies."""
        )
        chunk_size = st.slider("Chunk Size (characters):", 100, 1000, 300, 50)

        if st.button("📥 Chunk & Index Document"):
            tokenizer = get_tokenizer("gemini-2.5-pro")
            # Simple text chunking
            chunks = [doc_body[i:i+chunk_size] for i in range(0, len(doc_body), chunk_size)]
            with duckdb.connect(DB_PATH) as conn:
                for idx, chunk in enumerate(chunks):
                    t_count = tokenizer.count_tokens(chunk).total_tokens
                    conn.execute("""
                        INSERT OR REPLACE INTO rag_documents VALUES (?, ?, ?, ?, ?)
                    """, (f"{doc_name}_{idx}", doc_name, idx, chunk, t_count))
            st.success(f"Indexed {len(chunks)} chunks into DuckDB!")

    with col_search:
        st.markdown("##### 🔎 2. Search Indexed Chunks")
        search_query = st.text_input("Enter search keywords:", value="database analytical queries")
        
        with duckdb.connect(DB_PATH) as conn:
            doc_count = conn.execute("SELECT count(*) FROM rag_documents").fetchone()[0]
            st.caption(f"Currently indexing **{doc_count}** document chunks locally.")
    
            if search_query and doc_count > 0:
                # Full-text / keyword matching query in DuckDB
                terms = [f"%{t}%" for t in search_query.split() if len(t) > 2]
                if terms:
                    where_clause = " OR ".join(["content ILIKE ?" for _ in terms])
                    res = conn.execute(f"""
                        SELECT filename, chunk_index, token_count, content 
                        FROM rag_documents 
                        WHERE {where_clause}
                        LIMIT 5
                    """, terms).fetchall()
    
                    if res:
                        st.write(f"Found **{len(res)}** matching chunks:")
                        for r in res:
                            with st.expander(f"📌 {r[0]} (Chunk #{r[1]} | {r[2]} tokens)"):
                                st.write(r[3])
                    else:
                        st.info("No matching chunks found for that query.")

# ======================================================================
# TAB 3: Codebase Token Auditor
# ======================================================================
with tabs[2]:
    st.subheader("Scan Local Repository for Context & Token Optimization")
    st.write("Calculate token counts across your source files before feeding them into prompts or context windows.")

    default_repo_path = os.path.dirname(__file__)
    target_path = st.text_input("Project / Directory Path to Scan:", value=default_repo_path)
    file_extensions = st.multiselect("File types to include:", [".py", ".md", ".json", ".sql", ".sh", ".toml"], default=[".py", ".md", ".toml"])

    if st.button("📊 Scan Codebase"):
        target_dir = Path(target_path).expanduser()
        if not target_dir.exists():
            st.error(f"Path does not exist: {target_dir}")
        else:
            tokenizer = get_tokenizer("gemini-2.5-pro")
            scan_records = []
            
            with st.spinner("Scanning files and counting tokens..."):
                for root, dirs, files in os.walk(target_dir):
                    # Skip common noisy dirs
                    dirs[:] = [d for d in dirs if d not in [".git", ".venv", "__pycache__", "node_modules"]]
                    for file in files:
                        p = Path(root) / file
                        if p.suffix in file_extensions:
                            try:
                                content = p.read_text(encoding="utf-8", errors="ignore")
                                if content.strip():
                                    t_count = tokenizer.count_tokens(content).total_tokens
                                    scan_records.append({
                                        "File": p.name,
                                        "Relative Path": str(p.relative_to(target_dir)),
                                        "Extension": p.suffix,
                                        "Tokens": t_count,
                                        "Characters": len(content),
                                        "Lines": len(content.splitlines())
                                    })
                            except Exception:
                                pass

            if scan_records:
                df_code = pd.DataFrame(scan_records).sort_values("Tokens", ascending=False)
                tot_tokens = df_code["Tokens"].sum()
                tot_files = len(df_code)

                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.metric("Total Codebase Tokens", f"{tot_tokens:,}")
                with sc2:
                    st.metric("Total Files Scanned", f"{tot_files:,}")
                with sc3:
                    st.metric("Avg Tokens / File", f"{int(tot_tokens / tot_files):,}")

                # Treemap Visualization
                fig_treemap = px.treemap(
                    df_code,
                    path=["Extension", "File"],
                    values="Tokens",
                    color="Tokens",
                    color_continuous_scale="Blues",
                    title="Codebase Token Distribution"
                )
                st.plotly_chart(fig_treemap, use_container_width=True)

                st.dataframe(df_code, use_container_width=True)
            else:
                st.warning("No files found matching the selected criteria.")

# ======================================================================
# TAB 4: Offline Prompt Evaluation & Diff Comparator
# ======================================================================
with tabs[3]:
    st.subheader("Side-by-Side Prompt Evaluation & Validator")
    st.write("Compare different system prompts, test outputs, and measure deterministic criteria offline.")

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        st.markdown("##### Prompt Version A (Concise)")
        prompt_a = st.text_area("Template A:", height=140, value="Return JSON with keys: 'summary' and 'action_items'. Be extremely concise.")
    with pcol2:
        st.markdown("##### Prompt Version B (Detailed / Guardrailed)")
        prompt_b = st.text_area("Template B:", height=140, value="You are a principal engineer. Output strictly valid RFC 8259 JSON containing 'summary' and 'action_items'. Do not include markdown ticks.")

    tokenizer = get_tokenizer("gemini-2.5-pro")
    tokens_a = tokenizer.count_tokens(prompt_a).total_tokens
    tokens_b = tokenizer.count_tokens(prompt_b).total_tokens

    c_diff1, c_diff2 = st.columns(2)
    with c_diff1:
        st.metric("Prompt A Tokens", tokens_a)
    with c_diff2:
        st.metric("Prompt B Tokens", tokens_b, delta=f"{tokens_b - tokens_a} tokens")

    if models and st.button("🧪 Compare Model Responses Locally"):
        test_model = models[0]
        st.write(f"Testing on local model: **{test_model}**")
        
        with st.spinner("Generating responses for both versions..."):
            def query_ollama(text):
                try:
                    r = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={
                        "model": test_model, "prompt": text + "\nInput: Meeting held with DevOps to plan migration.", "stream": False
                    }, timeout=30)
                    return r.json().get("response", "")
                except Exception as e:
                    return str(e)

            out_a = query_ollama(prompt_a)
            out_b = query_ollama(prompt_b)

            rcol1, rcol2 = st.columns(2)
            with rcol1:
                st.markdown("**Output A:**")
                st.code(out_a, language="json")
            with rcol2:
                st.markdown("**Output B:**")
                st.code(out_b, language="json")

# ======================================================================
# TAB 5: DuckDB Analytics & SQL Explorer
# ======================================================================
with tabs[4]:
    st.subheader("Query Your Local Analytics Database (DuckDB)")
    st.write("All prompts, token counts, and TPS rates are logged locally to `local_analytics.duckdb`.")

    with duckdb.connect(DB_PATH) as conn:
        df_logs = conn.execute("SELECT * FROM prompt_logs ORDER BY timestamp DESC LIMIT 50").df()

    if not df_logs.empty:
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Total Invocations", len(df_logs))
        with d2:
            st.metric("Total Tokens", f"{df_logs['total_tokens'].sum():,}")
        with d3:
            avg_tps = df_logs['tokens_per_sec'].replace(0, pd.NA).mean()
            st.metric("Avg Speed (TPS)", f"{avg_tps:.1f}" if pd.notna(avg_tps) else "N/A")
        with d4:
            st.metric("Models Used", df_logs['model'].nunique())

        st.markdown("---")
        st.markdown("##### 🔍 Custom Local SQL Query")
        sql_input = st.text_area(
            "Execute SQL directly on DuckDB:",
            value="SELECT model, count(*) as runs, sum(total_tokens) as tokens, round(avg(tokens_per_sec), 1) as avg_tps FROM prompt_logs GROUP BY model",
            height=70
        )
        if st.button("Run SQL"):
            try:
                with duckdb.connect(DB_PATH) as conn:
                    res_df = conn.execute(sql_input).df()
                st.dataframe(res_df, use_container_width=True)
            except Exception as sql_err:
                st.error(f"SQL Error: {sql_err}")

        st.markdown("##### 📋 Recent Execution Records")
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("No prompt logs yet. Run a prompt in Tab 1 to start populating your local DuckDB analytical database!")
