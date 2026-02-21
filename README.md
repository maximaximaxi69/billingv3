# billingv3

Initial billing domain scaffolding with deterministic invoice total calculations.

## Quick start

```bash
python -m pytest
```

## Included now

- `InvoiceItem` dataclass for invoice lines
- `calculate_invoice_totals` helper for subtotal/tax/total
- Tests for normal and validation paths
