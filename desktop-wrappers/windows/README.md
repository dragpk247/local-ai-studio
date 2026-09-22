# Windows Desktop App Wrapper

This folder contains the wrapper script to package the Streamlit dashboard as a native Windows desktop application (an `.exe` file) using `pywebview` and `PyInstaller`.

## How to Build

1. **Install Dependencies**:
Ensure you have the required dependencies, plus the desktop packaging tools:
```bash
pip install -r ../../requirements.txt
pip install pywebview pyinstaller
```

2. **Run PyInstaller**:
Run the following command from the root of the repository (where `dashboard.py` is located) to package the application.
```bash
pyinstaller --onefile --windowed --copy-metadata streamlit --copy-metadata plotly --add-data "dashboard.py;." "desktop-wrappers/windows/main.py"
```

3. **Run the App**:
The compiled `.exe` will be located in the `dist/` folder. Simply double-click it to run the dashboard as a native Windows app!
