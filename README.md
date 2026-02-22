# billingv3 (CustomTkinter Desktop App)

A desktop billing app with a sidebar-based GUI inspired by invoice dashboards.

## Included functionality

- 3 invoice types:
  - Standard invoice
  - Proforma invoice
  - Recurring invoice
- Pavadzīme (delivery note)
- Bilingual UI support: English + Latvian (EN/LV switch)
- Client data storage (JSON on local disk)
- Document save/history view
- Sorting and searching across invoices and pavadzīmes
- Mark document as paid
- Existing invoice total logic preserved (`InvoiceItem`, tax, totals)

## Run (Windows)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python -m billing
```

## Data storage

Saved to:

- `data/billing_data.json`

## Run tests

```powershell
pip install -e .[dev]
python -m pytest
```


## Build a Windows .exe (PyInstaller)

If you see `ImportError: attempted relative import with no known parent package`, build from `run.py` instead of `billing/__main__.py`.

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name billingv3 --collect-all customtkinter run.py
```

Executable output:

- `dist\billingv3\billingv3.exe`


## Modern UI icon setup (required for icon buttons)

Create this folder in the project root:

- `assets/icons/`

Put PNG icons there with **transparent background** and these exact filenames:

- `assets/icons/new_document.png`
- `assets/icons/documents.png`
- `assets/icons/clients.png`
- `assets/icons/save.png`
- `assets/icons/add.png`
- `assets/icons/refresh.png`
- `assets/icons/paid.png`

Recommended icon specs:

- Format: `.png`
- Canvas: **24x24 px** (or 32x32 px)
- Monochrome icon (white/light) for dark theme
- Transparent background

The app renders icons at 18x18 on buttons. If a file is missing, the app still works (button shows text only).

## Updated .exe build command (includes icon/image assets)

```powershell
pyinstaller --noconfirm --clean --windowed --name billingv3 --collect-all customtkinter --collect-all PIL --add-data "assets;assets" run.py
```
