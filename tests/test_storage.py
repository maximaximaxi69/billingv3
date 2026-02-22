from datetime import date, timedelta
from decimal import Decimal

from billing.documents import Client, build_document
from billing.invoice import InvoiceItem
from billing.storage import BillingRepository, filter_and_sort_documents


def test_repository_saves_clients_and_documents(tmp_path):
    repo = BillingRepository(tmp_path / "billing_data.json")

    client = Client(name="Acme", registration_number="LV123", email="hello@acme.lv", address="Riga")
    repo.add_or_update_client(client)

    number = repo.next_document_number("invoice_standard")
    document = build_document(
        number=number,
        document_type="invoice_standard",
        language="lv",
        client=client,
        items=[InvoiceItem(description="Pakalpojums", quantity=2, unit_price=Decimal("50.00"))],
        tax_rate=Decimal("0.21"),
        due_date=date.today() + timedelta(days=7),
    )
    repo.add_document(document)

    assert repo.list_clients()[0].name == "Acme"
    loaded_docs = repo.list_documents()
    assert len(loaded_docs) == 1
    assert loaded_docs[0].number == number
    assert loaded_docs[0].totals()["total"] == Decimal("121.00")


def test_filter_and_mark_paid(tmp_path):
    repo = BillingRepository(tmp_path / "billing_data.json")
    client = Client(name="Beta", registration_number="LV999", email="a@b.lv", address="Liepaja")

    doc1 = build_document(
        number="INV-00001",
        document_type="invoice_standard",
        language="en",
        client=client,
        items=[InvoiceItem(description="Consulting", quantity=1, unit_price=Decimal("100.00"))],
        tax_rate=Decimal("0.00"),
        due_date=date.today() + timedelta(days=14),
    )
    doc2 = build_document(
        number="PAV-00001",
        document_type="delivery_note",
        language="lv",
        client=client,
        items=[InvoiceItem(description="Goods", quantity=1, unit_price=Decimal("10.00"))],
        tax_rate=Decimal("0.00"),
        due_date=date.today() + timedelta(days=14),
    )
    repo.add_document(doc1)
    repo.add_document(doc2)

    filtered = filter_and_sort_documents(repo.list_documents(), doc_type="delivery_note")
    assert len(filtered) == 1
    assert filtered[0].number == "PAV-00001"

    assert repo.mark_document_paid("INV-00001") is True
    paid_doc = [d for d in repo.list_documents() if d.number == "INV-00001"][0]
    assert paid_doc.status == "paid"
