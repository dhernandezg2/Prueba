import sys
import os
import threading
import time
import webbrowser
from streamlit.web import cli as stcli

def resource_path(rel_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

def open_browser():
    """Wait for the server to start and then open the browser"""
    time.sleep(3)
    webbrowser.open("http://localhost:8501")

if __name__ == "__main__":
    # Point to the internal app.py
    app_path = resource_path("app.py")
    
    # Configure Streamlit arguments
    # We simulate 'streamlit run app.py ...'
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",
        "--server.port=8501",
    ]
    
    print("Iniciando servidor Streamlit...")
    
    # Start the browser opener in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Streamlit (this blocks until the server method returns, which is usually never)
    try:
        sys.exit(stcli.main())
    except SystemExit:
        pass
