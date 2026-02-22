# billingv3 (CustomTkinter Desktop App)

Professional desktop invoicing app with clients, products, documents, settings, and PDF export.

## Workflow features

- Sidebar tabs: **New Document**, **Documents**, **Clients**, **Products**, **Settings**
- 3 invoice types + pavadzīme
- Clients with bank data: Bank, SWIFT, IBAN, Category
- Country-based client sorting/filter
- Product catalog with pre-defined descriptions and prices
- New Document view uses dropdowns from saved Clients and Products
- Company settings store logo path and company banking info
- PDF invoice generation with company logo in top-left
- Bilingual Latvian/English invoice labels in PDF output
- Latvian accounting total rows (Summa bez PVN, PVN %, KOPĀ, Saņemts avanss, Kopā apmaksai)

## Run (Windows)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
python -m billing
```

## Build EXE

```powershell
pyinstaller --noconfirm --clean --windowed --name billingv3 --collect-all customtkinter run.py
## Icon mapping and setup

Create folder:

- `assets/icons/`

Required PNG files (transparent background):

- `new_document.png` -> New Document button
- `documents.png` -> Documents button
- `clients.png` -> Clients button
- `add.png` -> Products button and add actions
- `settings.png` -> Settings button
- `save.png` -> Save actions
- `refresh.png` -> Refresh actions
- `paid.png` -> Mark-paid action

Icon spec:

- format: PNG
- size: 24x24 or 32x32 px
- app renders at 18x18 px

## Build EXE

```powershell
pyinstaller --noconfirm --clean --windowed --name billingv3 --collect-all customtkinter --collect-all PIL --add-data "assets;assets" run.py
```

## PDF dependency

PDF generation uses reportlab. If missing:

```powershell
pip install reportlab
```

## Tests

```powershell
pip install -e .[dev]
python -m pytest
```
