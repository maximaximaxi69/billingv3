from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class InvoiceItem:
    """A single line item on an invoice."""

    description: str
    quantity: int
    unit_price: Decimal

    def subtotal(self) -> Decimal:
        if self.quantity < 0:
            raise ValueError("quantity cannot be negative")
        if self.unit_price < 0:
            raise ValueError("unit_price cannot be negative")
        return (self.unit_price * self.quantity).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def calculate_invoice_totals(items: list[InvoiceItem], tax_rate: Decimal) -> dict[str, Decimal]:
    """Calculate subtotal, tax, and total for invoice items.

    tax_rate is expected as a fraction (e.g. 0.08 for 8%).
    """

    if tax_rate < 0:
        raise ValueError("tax_rate cannot be negative")

    subtotal = sum((item.subtotal() for item in items), Decimal("0.00"))
    tax = (subtotal * tax_rate).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    total = (subtotal + tax).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return {
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }
