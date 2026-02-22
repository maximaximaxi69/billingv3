# billingv3 (GUI App)

A beginner-friendly **desktop billing app** built with **CustomTkinter**.
It now has real windows, inputs, and buttons you can click.

## What this app does

- Add invoice items with description, quantity, and unit price
- Set tax rate (%)
- Click **Calculate Total** to get subtotal, tax, and total
- Clear all items with one button

## Run on Windows (step by step)

1. Install Python 3.11+ from python.org
2. Open PowerShell in the project folder
3. Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Install package + dependencies

```powershell
python -m pip install --upgrade pip
pip install -e .
```

5. Start the app window

```powershell
billingv3
```

Or:

```powershell
python -m billing
```

## Run tests

```powershell
pip install -e .[dev]
python -m pytest
```
