from decimal import Decimal

import pytest

from billing.invoice import InvoiceItem, calculate_invoice_totals


def test_calculate_invoice_totals():
    items = [
        InvoiceItem(description="Pro seat", quantity=3, unit_price=Decimal("29.99")),
        InvoiceItem(description="Setup", quantity=1, unit_price=Decimal("99.00")),
    ]

    totals = calculate_invoice_totals(items, Decimal("0.0825"))

    assert totals["subtotal"] == Decimal("188.97")
    assert totals["tax"] == Decimal("15.59")
    assert totals["total"] == Decimal("204.56")


def test_negative_quantity_raises():
    with pytest.raises(ValueError, match="quantity"):
        InvoiceItem(description="Bad", quantity=-1, unit_price=Decimal("1.00")).subtotal()


def test_negative_tax_rate_raises():
    items = [InvoiceItem(description="A", quantity=1, unit_price=Decimal("10.00"))]

    with pytest.raises(ValueError, match="tax_rate"):
        calculate_invoice_totals(items, Decimal("-0.01"))
