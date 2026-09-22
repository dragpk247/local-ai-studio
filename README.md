# ⚡ Local AI Engineering Studio

A 100% private, offline, and free local AI engineering dashboard built with **Streamlit**, **Ollama**, **DuckDB**, and **SentencePiece**.

No cloud dependencies, API keys, or subscription costs required.

---

## 🌟 Features

1. **🤖 Local Model Inference**: Connects to local [Ollama](https://ollama.com) models (`qwen2.5-coder`, `llama3.2`, etc.) to stream responses and measure token generation speed (TPS).
2. **📚 Local Document Search / RAG**: Split and index your private documents into a local **DuckDB** database with keyword and semantic search.
3. **🔍 Codebase Token Auditor**: Recursively scans any local project folder, counts tokens using offline SentencePiece tokenizers, and visualizes token distribution with a treemap before feeding code into context windows.
4. **⚖️ Prompt Comparator & Eval**: Compare prompt templates side-by-side and validate model outputs against JSON specifications.
5. **📊 DuckDB Analytics & SQL Explorer**: Stores every prompt, token count, and performance metric in an embedded DuckDB database (`local_analytics.duckdb`) with an in-app interactive SQL console.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- (Optional but recommended) [Ollama](https://ollama.com) running locally (`ollama serve`)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/local-ai-studio.git
cd local-ai-studio

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Dashboard
```bash
streamlit run dashboard.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🔒 Privacy & Local-First Design
All data, database files (`.duckdb`), and logs remain strictly on your local machine and are excluded from git version control.
