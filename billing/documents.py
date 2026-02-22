from __future__ import annotations

from dataclasses import asdict, dataclass
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
    advance_received: Decimal = Decimal("0.00")

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
            "advance_received": str(self.advance_received),
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
            advance_received=Decimal(data.get("advance_received", "0.00")),
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
    advance_received: Decimal = Decimal("0.00"),
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
        advance_received=advance_received,
    )


def generate_invoice_pdf(document: BillingDocument, settings: CompanySettings, output_path: Path) -> Path:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError as exc:
        raise RuntimeError("reportlab is required for PDF generation") from exc

    # REGISTER LATVIAN FONT (Ensure the .ttf file exists in your assets folder)
    font_path = Path("assets/DejaVuSans.ttf")
    if font_path.exists():
        pdfmetrics.registerFont(TTFont("LatvianFont", str(font_path)))
        pdfmetrics.registerFont(TTFont("LatvianFontBold", str(Path("assets/DejaVuSans-Bold.ttf"))))
        main_font = "LatvianFont"
        bold_font = "LatvianFontBold"
    else:
        # Fallback to Helvetica if font is missing (Characters will break!)
        main_font = "Helvetica"
        bold_font = "Helvetica-Bold"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # Header brand/logo (top-left)
    if settings.logo_path and Path(settings.logo_path).exists():
        c.drawImage(settings.logo_path, 40, height - 95, width=140, height=55, preserveAspectRatio=True, mask="auto")
    else:
        c.setFont(bold_font, 18)
        c.drawString(40, height - 55, "ARKA SILENT")

    title_map = {
        "invoice_standard": "GALA RĒĶINS / FINAL INVOICE",
        "invoice_proforma": "PROFORMA RĒĶINS / PROFORMA INVOICE",
        "invoice_recurring": "PERIODISKAIS RĒĶINS / RECURRING INVOICE",
        "delivery_note": "PAVADZĪME / DELIVERY NOTE",
    }
    doc_title = title_map.get(document.document_type, "RĒĶINS / INVOICE")

    c.setFont(bold_font, 16)
    c.drawRightString(width - 40, height - 52, doc_title.upper())
    c.setFont(bold_font, 13)
    c.drawRightString(width - 40, height - 72, f"NR. / NO.: {document.number}")

    # Bilingual meta block
    c.setFont(main_font, 10)
    c.drawString(40, height - 130, f"No / From: {settings.company_name}")
    c.drawString(40, height - 145, f"Reģ. nr. / Registration No: {settings.registration_number}")
    c.drawString(40, height - 160, f"Datums / Date: {document.issue_date.isoformat()}")

    c.drawString(320, height - 130, f"Kam / To: {document.client.name}")
    c.drawString(320, height - 145, f"Reģ. nr. / Registration No: {document.client.registration_number}")
    c.drawString(320, height - 160, f"Adrese / Address: {document.client.address}")

    # Items table (Latvian headers requested)
    table_top = height - 205
    c.setFont(bold_font, 10)
    c.drawString(45, table_top, "Nosaukums")
    c.drawString(320, table_top, "Daudz.")
    c.drawString(390, table_top, "Cena")
    c.drawString(480, table_top, "Summa")
    c.line(40, table_top - 4, width - 40, table_top - 4)

    y = table_top - 22
    c.setFont(main_font, 10)
    for item in document.items:
        c.drawString(45, y, item.description[:52])
        c.drawRightString(355, y, str(item.quantity))
        c.drawRightString(450, y, f"{item.unit_price:.2f}")
        c.drawRightString(555, y, f"{item.subtotal():.2f}")
        y -= 16

    totals = document.totals()
    y -= 8
    c.line(360, y + 6, width - 40, y + 6)

    def total_row(label: str, value: Decimal) -> None:
        nonlocal y
        c.drawString(365, y, label)
        c.drawRightString(555, y, f"{value:.2f}")
        y -= 15

    c.setFont(main_font, 10)
    total_row("Summa bez PVN", totals["subtotal"])
    vat_percent = (document.tax_rate * Decimal("100")).quantize(Decimal("0.01"))
    total_row(f"PVN {vat_percent}%", totals["tax"])
    total_row("KOPĀ", totals["total"])

    if document.document_type == "invoice_standard":
        total_row("Saņemts avanss", -document.advance_received)
        payable = (totals["total"] - document.advance_received).quantize(Decimal("0.01"))
        c.setFont(bold_font, 11)
        c.drawString(365, y, "Kopā apmaksai")
        c.drawRightString(555, y, f"{payable:.2f}")
        y -= 18

    # Banking block at bottom
    bank_y = 130
    c.setFont(bold_font, 10)
    c.drawString(40, bank_y + 35, "Bankas informācija / Banking details")
    c.setFont(main_font, 10)
    c.drawString(40, bank_y + 20, f"Banka / Bank: {settings.bank}")
    c.drawString(40, bank_y + 5, f"BIC/SWIFT: {settings.swift}")
    c.drawString(40, bank_y - 10, f"Konta Nr / IBAN: {settings.iban}")

    # Footer legal disclaimer
    c.setFont(main_font, 9)
    c.drawCentredString(width / 2, 35, "Dokuments sagatavots elektroniski un derīgs bez paraksta")

    c.showPage()
    c.save()
    return output_path
