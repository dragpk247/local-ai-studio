import os
import sys
import time
import webview
import subprocess
import urllib.request
import logging

# Dashboard dependencies (imported here so PyInstaller bundles them)
import streamlit
import pandas
import plotly.express
import requests
import duckdb
try:
    from google.genai.local_tokenizer import LocalTokenizer
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)

def wait_for_server():
    while True:
        try:
            urllib.request.urlopen("http://localhost:8501/_stcore/health")
            break
        except Exception:
            time.sleep(0.5)

def main():
    if getattr(sys, 'frozen', False):
        app_path = sys._MEIPASS
        dashboard_path = os.path.join(app_path, "dashboard.py")
        cmd = [sys.executable, "--run-streamlit"]
    else:
        app_path = os.path.dirname(os.path.abspath(__file__))
        dashboard_path = os.path.join(app_path, "dashboard.py")
        cmd = [sys.executable, __file__, "--run-streamlit"]

    if len(sys.argv) > 1 and sys.argv[1] == '--run-streamlit':
        # We are in the subprocess, run streamlit
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w')
        import streamlit.web.cli as stcli
        sys.argv = ["streamlit", "run", dashboard_path, "--server.headless", "true", "--server.port", "8501", "--global.developmentMode", "false"]
        sys.exit(stcli.main())

    # We are in the main process
    # Start the subprocess with redirected I/O for windowed mode
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    # Wait for Streamlit to become healthy
    wait_for_server()

    # Create the webview window
    window = webview.create_window('Local AI Studio', 'http://localhost:8501', width=1280, height=800)
    
    def on_minimized():
        logging.info("Window minimized. Auto-unloading Ollama models...")
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r.status_code == 200:
                for m in r.json().get("models", []):
                    requests.post("http://localhost:11434/api/generate", json={"model": m["name"], "keep_alive": 0}, timeout=2)
        except Exception as e:
            logging.error(f"Failed to auto-unload models: {e}")

    window.events.minimized += on_minimized
    webview.start()
    
    # Once webview is closed, terminate the subprocess
    proc.terminate()
    sys.exit(0)

if __name__ == '__main__':
    # When packaged, PyInstaller sets sys.frozen
    # multiprocessing on Windows sometimes requires this:
    import multiprocessing
    multiprocessing.freeze_support()
    main()
