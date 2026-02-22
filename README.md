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
