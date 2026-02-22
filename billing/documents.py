from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from .invoice import InvoiceItem, calculate_invoice_totals


DOCUMENT_TYPES = {
    "invoice_standard",
    "invoice_proforma",
    "invoice_recurring",
    "delivery_note",
}


@dataclass(frozen=True)
class Client:
    name: str
    registration_number: str
    email: str
    address: str


@dataclass(frozen=True)
class BillingDocument:
    number: str
    document_type: str
    language: str
    client: Client
    items: list[InvoiceItem]
    tax_rate: Decimal
    issue_date: date
    due_date: date
    status: str = "open"

    def totals(self) -> dict[str, Decimal]:
        return calculate_invoice_totals(self.items, self.tax_rate)

    def to_dict(self) -> dict[str, Any]:
        totals = self.totals()
        return {
            "number": self.number,
            "document_type": self.document_type,
            "language": self.language,
            "client": asdict(self.client),
            "items": [
                {
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                }
                for item in self.items
            ],
            "tax_rate": str(self.tax_rate),
            "issue_date": self.issue_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "status": self.status,
            "totals": {k: str(v) for k, v in totals.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BillingDocument":
        return cls(
            number=data["number"],
            document_type=data["document_type"],
            language=data["language"],
            client=Client(**data["client"]),
            items=[
                InvoiceItem(
                    description=item["description"],
                    quantity=int(item["quantity"]),
                    unit_price=Decimal(item["unit_price"]),
                )
                for item in data["items"]
            ],
            tax_rate=Decimal(data["tax_rate"]),
            issue_date=date.fromisoformat(data["issue_date"]),
            due_date=date.fromisoformat(data["due_date"]),
            status=data.get("status", "open"),
        )


def build_document(
    number: str,
    document_type: str,
    language: str,
    client: Client,
    items: list[InvoiceItem],
    tax_rate: Decimal,
    due_date: date,
    issue_date: date | None = None,
) -> BillingDocument:
    if document_type not in DOCUMENT_TYPES:
        raise ValueError("Unsupported document_type")
    if language not in {"en", "lv"}:
        raise ValueError("language must be en or lv")
    if not items:
        raise ValueError("At least one item is required")

    normalized_issue_date = issue_date or date.today()
    if due_date < normalized_issue_date:
        raise ValueError("due_date must not be earlier than issue_date")

    return BillingDocument(
        number=number,
        document_type=document_type,
        language=language,
        client=client,
        items=items,
        tax_rate=tax_rate,
        issue_date=normalized_issue_date,
        due_date=due_date,
    )
