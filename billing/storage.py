from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from decimal import Decimal

from .documents import BillingDocument, Client, CompanySettings, Product


class BillingRepository:
    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or Path("data") / "billing_data.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write({"clients": [], "products": [], "documents": [], "settings": asdict(CompanySettings())})

    def _read(self) -> dict[str, Any]:
        return json.loads(self.storage_path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, Any]) -> None:
        self.storage_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_clients(self, country: str | None = None) -> list[Client]:
        clients = [Client(**entry) for entry in self._read()["clients"]]
        if country:
            clients = [c for c in clients if c.country.lower() == country.lower()]
        return sorted(clients, key=lambda c: (c.country.lower(), c.name.lower()))

    def add_or_update_client(self, client: Client) -> None:
        data = self._read()
        clients = [entry for entry in data["clients"] if entry["registration_number"] != client.registration_number]
        clients.append(asdict(client))
        data["clients"] = clients
        self._write(data)

    def list_products(self) -> list[Product]:
        products = [Product(name=p["name"], description=p["description"], unit_price=Decimal(p["unit_price"])) for p in self._read()["products"]]
        return sorted(products, key=lambda p: p.name.lower())

    def add_or_update_product(self, product: Product) -> None:
        data = self._read()
        products = [p for p in data["products"] if p["name"].lower() != product.name.lower()]
        products.append({"name": product.name, "description": product.description, "unit_price": str(product.unit_price)})
        data["products"] = products
        self._write(data)

    def get_settings(self) -> CompanySettings:
        settings = self._read().get("settings", {})
        return CompanySettings(**{**asdict(CompanySettings()), **settings})

    def save_settings(self, settings: CompanySettings) -> None:
        data = self._read()
        data["settings"] = asdict(settings)
        self._write(data)

    def list_documents(self) -> list[BillingDocument]:
        return [BillingDocument.from_dict(entry) for entry in self._read()["documents"]]

    def next_document_number(self, document_type: str) -> str:
        prefix_map = {
            "invoice_standard": "INV",
            "invoice_proforma": "PRO",
            "invoice_recurring": "REC",
            "delivery_note": "PAV",
        }
        prefix = prefix_map[document_type]
        current = [doc for doc in self.list_documents() if doc.number.startswith(prefix)]
        return f"{prefix}-{len(current)+1:05d}"

    def add_document(self, document: BillingDocument) -> None:
        data = self._read()
        documents = [d for d in data["documents"] if d["number"] != document.number]
        documents.append(document.to_dict())
        data["documents"] = documents
        self._write(data)

    def mark_document_paid(self, number: str) -> bool:
        data = self._read()
        updated = False
        for d in data["documents"]:
            if d["number"] == number:
                d["status"] = "paid"
                updated = True
        if updated:
            self._write(data)
        return updated


def filter_and_sort_documents(
    documents: list[BillingDocument],
    *,
    doc_type: str = "all",
    search: str = "",
    sort_by: str = "issue_date_desc",
) -> list[BillingDocument]:
    result = documents
    if doc_type != "all":
        result = [doc for doc in result if doc.document_type == doc_type]

    q = search.strip().lower()
    if q:
        result = [doc for doc in result if q in doc.number.lower() or q in doc.client.name.lower() or q in doc.client.country.lower()]

    keys = {
        "issue_date_desc": lambda d: d.issue_date.toordinal(),
        "issue_date_asc": lambda d: d.issue_date.toordinal(),
        "client_asc": lambda d: d.client.name.lower(),
        "country_asc": lambda d: d.client.country.lower(),
        "number_asc": lambda d: d.number,
    }
    reverse = sort_by == "issue_date_desc"
    if sort_by not in keys:
        sort_by = "issue_date_desc"
        reverse = True
    return sorted(result, key=keys[sort_by], reverse=reverse)
