from datetime import date, timedelta
from decimal import Decimal

from billing.documents import Client, CompanySettings, Product, build_document
from billing.invoice import InvoiceItem
from billing.storage import BillingRepository, filter_and_sort_documents


def make_client(name: str, reg: str, country: str = "Latvia") -> Client:
    return Client(
        name=name,
        registration_number=reg,
        email=f"{name.lower()}@example.com",
        address="Riga",
        country=country,
        bank="Swedbank",
        swift="HABALV22",
        iban="LV00HABA0000000000000",
        category="Direct",
    )


def test_repository_saves_clients_products_documents_and_settings(tmp_path):
    repo = BillingRepository(tmp_path / "billing_data.json")

    client = make_client("Acme", "LV123")
    repo.add_or_update_client(client)

    repo.add_or_update_product(Product(name="Consulting", description="Monthly service", unit_price=Decimal("50.00")))
    repo.save_settings(CompanySettings(company_name="MyCo", registration_number="4000", bank="SEB", swift="UNLALV2X", iban="LV00TEST", logo_path="logo.png"))

    number = repo.next_document_number("invoice_standard")
    document = build_document(
        number=number,
        document_type="invoice_standard",
        language="lv",
        client=client,
        items=[InvoiceItem(description="Monthly service", quantity=2, unit_price=Decimal("50.00"))],
        tax_rate=Decimal("0.21"),
        due_date=date.today() + timedelta(days=7),
    )
    repo.add_document(document)

    assert repo.list_clients()[0].name == "Acme"
    assert repo.list_products()[0].name == "Consulting"
    assert repo.get_settings().company_name == "MyCo"
    loaded_docs = repo.list_documents()
    assert loaded_docs[0].totals()["total"] == Decimal("121.00")


def test_filter_country_sort_and_mark_paid(tmp_path):
    repo = BillingRepository(tmp_path / "billing_data.json")
    client_lv = make_client("Beta", "LV999", "Latvia")
    client_ee = make_client("Alpha", "EE999", "Estonia")
    repo.add_or_update_client(client_lv)
    repo.add_or_update_client(client_ee)

    doc1 = build_document(
        number="INV-00001",
        document_type="invoice_standard",
        language="en",
        client=client_lv,
        items=[InvoiceItem(description="Consulting", quantity=1, unit_price=Decimal("100.00"))],
        tax_rate=Decimal("0.00"),
        due_date=date.today() + timedelta(days=14),
    )
    doc2 = build_document(
        number="PAV-00001",
        document_type="delivery_note",
        language="lv",
        client=client_ee,
        items=[InvoiceItem(description="Goods", quantity=1, unit_price=Decimal("10.00"))],
        tax_rate=Decimal("0.00"),
        due_date=date.today() + timedelta(days=14),
    )
    repo.add_document(doc1)
    repo.add_document(doc2)

    assert [c.country for c in repo.list_clients()] == ["Estonia", "Latvia"]
    assert len(repo.list_clients("Latvia")) == 1

    filtered = filter_and_sort_documents(repo.list_documents(), doc_type="delivery_note", sort_by="country_asc")
    assert filtered[0].number == "PAV-00001"

    assert repo.mark_document_paid("INV-00001") is True
    paid_doc = [d for d in repo.list_documents() if d.number == "INV-00001"][0]
    assert paid_doc.status == "paid"
