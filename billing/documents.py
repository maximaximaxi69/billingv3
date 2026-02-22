from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from .invoice import InvoiceItem, calculate_invoice_totals

DOCUMENT_TYPES = {
    "invoice_standard",
    "invoice_proforma",
    "invoice_recurring",
    "delivery_note",
}

CLIENT_CATEGORIES = {"Distributor", "Direct", "Other"}


@dataclass(frozen=True)
class Client:
    name: str
    registration_number: str
    email: str
    address: str
    country: str
    bank: str
    swift: str
    iban: str
    category: str = "Other"


@dataclass(frozen=True)
class Product:
    name: str
    description: str
    unit_price: Decimal


@dataclass(frozen=True)
class CompanySettings:
    company_name: str = ""
    registration_number: str = ""
    bank: str = ""
    swift: str = ""
    iban: str = ""
    logo_path: str = ""


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
    if client.category not in CLIENT_CATEGORIES:
        raise ValueError("Unsupported client category")

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


def generate_invoice_pdf(document: BillingDocument, settings: CompanySettings, output_path: Path) -> Path:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("reportlab is required for PDF generation") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    if settings.logo_path and Path(settings.logo_path).exists():
        c.drawImage(settings.logo_path, 40, height - 110, width=120, height=60, preserveAspectRatio=True, mask="auto")

    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 40, f"Invoice {document.number}")

    c.setFont("Helvetica", 10)
    c.drawString(40, height - 140, f"From: {settings.company_name}")
    c.drawString(40, height - 155, f"Reg No: {settings.registration_number}")
    c.drawString(40, height - 170, f"Bank: {settings.bank}")
    c.drawString(40, height - 185, f"SWIFT: {settings.swift}  IBAN: {settings.iban}")

    c.drawString(320, height - 140, f"To: {document.client.name}")
    c.drawString(320, height - 155, f"Reg No: {document.client.registration_number}")
    c.drawString(320, height - 170, document.client.address)
    c.drawString(320, height - 185, f"{document.client.country} | {document.client.category}")

    y = height - 230
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Description")
    c.drawString(300, y, "Qty")
    c.drawString(360, y, "Unit")
    c.drawString(440, y, "Subtotal")
    y -= 18
    c.setFont("Helvetica", 10)

    for item in document.items:
        c.drawString(40, y, item.description[:45])
        c.drawString(300, y, str(item.quantity))
        c.drawString(360, y, f"{item.unit_price:.2f}")
        c.drawString(440, y, f"{item.subtotal():.2f}")
        y -= 16

    totals = document.totals()
    y -= 12
    c.setFont("Helvetica-Bold", 11)
    c.drawString(360, y, "Subtotal:")
    c.drawString(440, y, f"{totals['subtotal']:.2f}")
    y -= 16
    c.drawString(360, y, "Tax:")
    c.drawString(440, y, f"{totals['tax']:.2f}")
    y -= 16
    c.drawString(360, y, "Total:")
    c.drawString(440, y, f"{totals['total']:.2f}")

    c.showPage()
    c.save()
    return output_path
