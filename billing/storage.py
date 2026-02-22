from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .documents import BillingDocument, Client


class BillingRepository:
    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or Path("data") / "billing_data.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write({"clients": [], "documents": []})

    def _read(self) -> dict[str, Any]:
        return json.loads(self.storage_path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, Any]) -> None:
        self.storage_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_clients(self) -> list[Client]:
        data = self._read()
        return [Client(**entry) for entry in data["clients"]]

    def add_or_update_client(self, client: Client) -> None:
        data = self._read()
        clients = [entry for entry in data["clients"] if entry["registration_number"] != client.registration_number]
        clients.append(asdict(client))
        data["clients"] = sorted(clients, key=lambda x: x["name"].lower())
        self._write(data)

    def list_documents(self) -> list[BillingDocument]:
        data = self._read()
        return [BillingDocument.from_dict(entry) for entry in data["documents"]]

    def next_document_number(self, document_type: str) -> str:
        prefix_map = {
            "invoice_standard": "INV",
            "invoice_proforma": "PRO",
            "invoice_recurring": "REC",
            "delivery_note": "PAV",
        }
        prefix = prefix_map[document_type]
        docs = self.list_documents()
        current = [doc for doc in docs if doc.number.startswith(prefix)]
        serial = len(current) + 1
        return f"{prefix}-{serial:05d}"

    def add_document(self, document: BillingDocument) -> None:
        data = self._read()
        docs = [entry for entry in data["documents"] if entry["number"] != document.number]
        docs.append(document.to_dict())
        data["documents"] = docs
        self._write(data)

    def mark_document_paid(self, number: str) -> bool:
        data = self._read()
        updated = False
        for entry in data["documents"]:
            if entry["number"] == number:
                entry["status"] = "paid"
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

    lowered = search.strip().lower()
    if lowered:
        result = [
            doc
            for doc in result
            if lowered in doc.number.lower()
            or lowered in doc.client.name.lower()
            or lowered in doc.client.registration_number.lower()
        ]

    key_map = {
        "issue_date_desc": lambda d: d.issue_date.toordinal(),
        "issue_date_asc": lambda d: d.issue_date.toordinal(),
        "client_asc": lambda d: d.client.name.lower(),
        "number_asc": lambda d: d.number,
    }

    reverse = sort_by == "issue_date_desc"
    if sort_by not in key_map:
        sort_by = "issue_date_desc"
        reverse = True

    return sorted(result, key=key_map[sort_by], reverse=reverse)
