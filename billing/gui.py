from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from .documents import Client, CompanySettings, Product, build_document, generate_invoice_pdf
from .invoice import InvoiceItem
from .storage import BillingRepository, filter_and_sort_documents

DOC_TYPE_LABELS = {
    "invoice_standard": "Invoice - Standard",
    "invoice_proforma": "Invoice - Proforma",
    "invoice_recurring": "Invoice - Recurring",
    "delivery_note": "Pavadzīme",
}


class BillingApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Billing Desktop")
        self.geometry("1480x900")

        ctk.set_appearance_mode("dark")

        self.palette = {
            "bg": "#0f1724",
            "sidebar": "#131e2f",
            "panel": "#18263a",
            "card": "#1e2f47",
            "accent": "#4f7cff",
            "accent_hover": "#6690ff",
            "success": "#12b981",
            "text": "#e9eef9",
            "muted": "#9cb0cc",
            "border": "#334962",
        }
        self.configure(fg_color=self.palette["bg"])

        self.repo = BillingRepository()
        self.icons = self._load_icons()
        self.current_items: list[InvoiceItem] = []

        self._build_layout()
        self._load_settings_to_form()
        self._refresh_clients()
        self._refresh_products()
        self._refresh_documents()
        self._refresh_dropdowns()

    def _load_icons(self) -> dict[str, ctk.CTkImage | None]:
        icon_files = {
            "new": "new_document.png",
            "docs": "documents.png",
            "clients": "clients.png",
            "products": "add.png",
            "settings": "settings.png",
            "save": "save.png",
            "add": "add.png",
            "refresh": "refresh.png",
            "paid": "paid.png",
            "pdf": "documents.png",
        }
        icon_dir = Path("assets/icons")
        out: dict[str, ctk.CTkImage | None] = {}
        for key, filename in icon_files.items():
            p = icon_dir / filename
            if p.exists():
                img = Image.open(p)
                out[key] = ctk.CTkImage(light_image=img, dark_image=img, size=(18, 18))
            else:
                out[key] = None
        return out

    def _card(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=self.palette["card"], corner_radius=16, border_width=1, border_color=self.palette["border"])
        ctk.CTkLabel(card, text=title, text_color=self.palette["text"], font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=18, pady=(14, 10))
        return card

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, fg_color=self.palette["sidebar"], width=270, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="Billing Pro", font=ctk.CTkFont(size=32, weight="bold"), text_color=self.palette["text"]).pack(anchor="w", padx=24, pady=(28, 2))
        ctk.CTkLabel(sidebar, text="Professional invoicing workflow", text_color=self.palette["muted"]).pack(anchor="w", padx=24, pady=(0, 16))

        self.nav_buttons = {}
        for key, label, icon in [
            ("new", "New Document", "new"),
            ("docs", "Documents", "docs"),
            ("clients", "Clients", "clients"),
            ("products", "Products", "products"),
            ("settings", "Settings", "settings"),
        ]:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                image=self.icons[icon],
                anchor="w",
                fg_color=self.palette["card"],
                hover_color=self.palette["accent_hover"],
                height=42,
                corner_radius=12,
                command=lambda k=key: self._show_view(k),
            )
            btn.pack(fill="x", padx=20, pady=7)
            self.nav_buttons[key] = btn

        self.message_label = ctk.CTkLabel(sidebar, text="", text_color="#fca5a5", wraplength=220, justify="left")
        self.message_label.pack(anchor="w", padx=22, pady=(24, 0))

        self.content = ctk.CTkFrame(self, fg_color=self.palette["panel"], corner_radius=20)
        self.content.grid(row=0, column=1, sticky="nsew", padx=22, pady=20)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.views = {
            "new": self._build_new_view(),
            "docs": self._build_docs_view(),
            "clients": self._build_clients_view(),
            "products": self._build_products_view(),
            "settings": self._build_settings_view(),
        }
        self._show_view("new")

    def _show_view(self, key: str) -> None:
        for frame in self.views.values():
            frame.grid_forget()
        self.views[key].grid(row=0, column=0, sticky="nsew")

    def _build_new_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure((0, 1), weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top = self._card(frame, "New Document")
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 10))
        top.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(top, text="Document Type", text_color=self.palette["muted"]).grid(row=1, column=0, padx=18, pady=8, sticky="w")
        self.doc_type_menu = ctk.CTkOptionMenu(top, values=list(DOC_TYPE_LABELS.keys()))
        self.doc_type_menu.set("invoice_standard")
        self.doc_type_menu.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(top, text="Tax %", text_color=self.palette["muted"]).grid(row=1, column=2, padx=18, pady=8, sticky="w")
        self.tax_entry = ctk.CTkEntry(top)
        self.tax_entry.insert(0, "21")
        self.tax_entry.grid(row=1, column=3, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(top, text="Due Days", text_color=self.palette["muted"]).grid(row=2, column=2, padx=18, pady=(0, 16), sticky="w")
        self.due_days_entry = ctk.CTkEntry(top)
        self.due_days_entry.insert(0, "14")
        self.due_days_entry.grid(row=2, column=3, padx=10, pady=(0, 16), sticky="ew")

        client_card = self._card(frame, "Select Client")
        client_card.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(0, 12))
        client_card.grid_columnconfigure(0, weight=1)

        self.client_dropdown = ctk.CTkOptionMenu(client_card, values=["No clients yet"])
        self.client_dropdown.grid(row=1, column=0, padx=18, pady=(6, 18), sticky="ew")

        item_card = self._card(frame, "Select Product")
        item_card.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=(0, 12))
        item_card.grid_columnconfigure(1, weight=1)
        item_card.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(item_card, text="Product", text_color=self.palette["muted"]).grid(row=1, column=0, padx=18, pady=8, sticky="w")
        self.product_dropdown = ctk.CTkOptionMenu(item_card, values=["No products yet"])
        self.product_dropdown.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(item_card, text="Quantity", text_color=self.palette["muted"]).grid(row=2, column=0, padx=18, pady=8, sticky="w")
        self.qty_entry = ctk.CTkEntry(item_card)
        self.qty_entry.insert(0, "1")
        self.qty_entry.grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        self.add_selected_product_btn = ctk.CTkButton(item_card, text="Add Product", image=self.icons["add"], fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], command=self._add_selected_product)
        self.add_selected_product_btn.grid(row=3, column=0, columnspan=2, padx=18, pady=10, sticky="ew")

        self.items_box = ctk.CTkTextbox(item_card)
        self.items_box.grid(row=4, column=0, columnspan=2, padx=18, pady=(2, 18), sticky="nsew")
        self.items_box.configure(state="disabled")

        bottom = ctk.CTkFrame(frame, fg_color="transparent")
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 16))
        bottom.grid_columnconfigure((0, 1), weight=1)

        self.save_doc_btn = ctk.CTkButton(bottom, text="Save Document", image=self.icons["save"], fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], height=44, command=self._save_document)
        self.save_doc_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.pdf_btn = ctk.CTkButton(bottom, text="Generate PDF", image=self.icons["pdf"], fg_color=self.palette["success"], hover_color="#34d399", height=44, command=self._generate_latest_pdf)
        self.pdf_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        return frame

    def _build_docs_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        filter_card = self._card(frame, "Documents")
        filter_card.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        filter_card.grid_columnconfigure((1, 3), weight=1)

        self.filter_type = ctk.CTkOptionMenu(filter_card, values=["all", *DOC_TYPE_LABELS.keys()])
        self.filter_type.set("all")
        self.filter_type.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")
        self.search_entry = ctk.CTkEntry(filter_card, placeholder_text="Search")
        self.search_entry.grid(row=1, column=1, padx=8, pady=(0, 16), sticky="ew")
        self.sort_menu = ctk.CTkOptionMenu(filter_card, values=["issue_date_desc", "issue_date_asc", "client_asc", "country_asc", "number_asc"])
        self.sort_menu.set("issue_date_desc")
        self.sort_menu.grid(row=1, column=2, padx=8, pady=(0, 16), sticky="ew")
        ctk.CTkButton(filter_card, text="Refresh", image=self.icons["refresh"], fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], command=self._refresh_documents).grid(row=1, column=3, padx=16, pady=(0, 16), sticky="ew")

        self.docs_box = ctk.CTkTextbox(frame)
        self.docs_box.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")
        self.docs_box.configure(state="disabled")

        return frame

    def _build_clients_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure((0, 1), weight=1)
        frame.grid_rowconfigure(1, weight=1)

        form = self._card(frame, "Client Management")
        form.grid(row=0, column=0, padx=(16, 8), pady=16, sticky="nsew")
        form.grid_columnconfigure(1, weight=1)

        def add_row(r: int, label: str):
            ctk.CTkLabel(form, text=label, text_color=self.palette["muted"]).grid(row=r, column=0, padx=16, pady=7, sticky="w")
            entry = ctk.CTkEntry(form)
            entry.grid(row=r, column=1, padx=10, pady=7, sticky="ew")
            return entry

        self.client_name_entry = add_row(1, "Name")
        self.client_reg_entry = add_row(2, "Reg No")
        self.client_email_entry = add_row(3, "Email")
        self.client_address_entry = add_row(4, "Address")
        self.client_country_entry = add_row(5, "Country")
        self.client_bank_entry = add_row(6, "Bank")
        self.client_swift_entry = add_row(7, "SWIFT")
        self.client_iban_entry = add_row(8, "IBAN")

        ctk.CTkLabel(form, text="Category", text_color=self.palette["muted"]).grid(row=9, column=0, padx=16, pady=7, sticky="w")
        self.client_category_menu = ctk.CTkOptionMenu(form, values=["Distributor", "Direct", "Other"])
        self.client_category_menu.set("Other")
        self.client_category_menu.grid(row=9, column=1, padx=10, pady=7, sticky="ew")

        ctk.CTkButton(form, text="Save Client", image=self.icons["save"], fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], command=self._save_client).grid(row=10, column=0, columnspan=2, padx=16, pady=(12, 16), sticky="ew")

        list_card = self._card(frame, "Clients (sorted by country)")
        list_card.grid(row=0, column=1, padx=(8, 16), pady=16, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(2, weight=1)

        self.country_filter_menu = ctk.CTkOptionMenu(list_card, values=["All"])
        self.country_filter_menu.set("All")
        self.country_filter_menu.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        ctk.CTkButton(list_card, text="Apply Country Sort", image=self.icons["refresh"], command=self._refresh_clients).grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")

        self.clients_box = ctk.CTkTextbox(list_card)
        self.clients_box.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.clients_box.configure(state="disabled")

        return frame

    def _build_products_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure((0, 1), weight=1)
        frame.grid_rowconfigure(0, weight=1)

        form = self._card(frame, "Products")
        form.grid(row=0, column=0, padx=(16, 8), pady=16, sticky="nsew")
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Name", text_color=self.palette["muted"]).grid(row=1, column=0, padx=16, pady=8, sticky="w")
        self.product_name_entry = ctk.CTkEntry(form)
        self.product_name_entry.grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(form, text="Description", text_color=self.palette["muted"]).grid(row=2, column=0, padx=16, pady=8, sticky="w")
        self.product_desc_entry = ctk.CTkEntry(form)
        self.product_desc_entry.grid(row=2, column=1, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(form, text="Unit Price", text_color=self.palette["muted"]).grid(row=3, column=0, padx=16, pady=8, sticky="w")
        self.product_price_entry = ctk.CTkEntry(form)
        self.product_price_entry.grid(row=3, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkButton(form, text="Save Product", image=self.icons["save"], fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], command=self._save_product).grid(row=4, column=0, columnspan=2, padx=16, pady=14, sticky="ew")

        list_card = self._card(frame, "Saved Products")
        list_card.grid(row=0, column=1, padx=(8, 16), pady=16, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)

        self.products_box = ctk.CTkTextbox(list_card)
        self.products_box.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.products_box.configure(state="disabled")
        return frame

    def _build_settings_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)

        card = self._card(frame, "My Company Settings")
        card.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        def row(r: int, label: str):
            ctk.CTkLabel(card, text=label, text_color=self.palette["muted"]).grid(row=r, column=0, padx=16, pady=8, sticky="w")
            e = ctk.CTkEntry(card)
            e.grid(row=r, column=1, padx=10, pady=8, sticky="ew")
            return e

        self.set_company_name = row(1, "Company Name")
        self.set_reg = row(2, "Reg No")
        self.set_bank = row(3, "Bank")
        self.set_swift = row(4, "SWIFT")
        self.set_iban = row(5, "IBAN")
        self.set_logo = row(6, "Logo File Path")

        ctk.CTkButton(card, text="Save Settings", image=self.icons["save"], fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], command=self._save_settings).grid(row=7, column=0, columnspan=2, padx=16, pady=16, sticky="ew")
        return frame

    def _msg(self, text: str) -> None:
        self.message_label.configure(text=text)

    def _save_client(self) -> None:
        try:
            client = Client(
                name=self.client_name_entry.get().strip(),
                registration_number=self.client_reg_entry.get().strip(),
                email=self.client_email_entry.get().strip(),
                address=self.client_address_entry.get().strip(),
                country=self.client_country_entry.get().strip(),
                bank=self.client_bank_entry.get().strip(),
                swift=self.client_swift_entry.get().strip(),
                iban=self.client_iban_entry.get().strip(),
                category=self.client_category_menu.get(),
            )
        except Exception:
            self._msg("Invalid client data")
            return
        if not client.name or not client.registration_number:
            self._msg("Client name and reg number required")
            return
        self.repo.add_or_update_client(client)
        self._refresh_clients()
        self._refresh_dropdowns()
        self._msg("Client saved")

    def _refresh_clients(self) -> None:
        country = self.country_filter_menu.get() if hasattr(self, "country_filter_menu") else "All"
        selected_country = None if country in (None, "All") else country
        clients = self.repo.list_clients(selected_country)

        countries = sorted({c.country for c in self.repo.list_clients() if c.country})
        self.country_filter_menu.configure(values=["All", *countries])
        if country in ["All", *countries]:
            self.country_filter_menu.set(country)
        else:
            self.country_filter_menu.set("All")

        self.clients_box.configure(state="normal")
        self.clients_box.delete("1.0", "end")
        for c in clients:
            self.clients_box.insert("end", f"{c.country} | {c.name} | {c.category} | {c.bank} | {c.swift} | {c.iban}\n")
        self.clients_box.configure(state="disabled")

    def _save_product(self) -> None:
        try:
            product = Product(
                name=self.product_name_entry.get().strip(),
                description=self.product_desc_entry.get().strip(),
                unit_price=Decimal(self.product_price_entry.get().strip()),
            )
        except InvalidOperation:
            self._msg("Unit price must be numeric")
            return
        if not product.name:
            self._msg("Product name required")
            return
        self.repo.add_or_update_product(product)
        self._refresh_products()
        self._refresh_dropdowns()
        self._msg("Product saved")

    def _refresh_products(self) -> None:
        products = self.repo.list_products()
        self.products_box.configure(state="normal")
        self.products_box.delete("1.0", "end")
        for p in products:
            self.products_box.insert("end", f"{p.name} | {p.description} | {p.unit_price:.2f}\n")
        self.products_box.configure(state="disabled")

    def _refresh_dropdowns(self) -> None:
        clients = self.repo.list_clients()
        products = self.repo.list_products()
        client_values = [f"{c.name} ({c.registration_number})" for c in clients] or ["No clients yet"]
        product_values = [f"{p.name} - {p.unit_price:.2f}" for p in products] or ["No products yet"]
        self.client_dropdown.configure(values=client_values)
        self.client_dropdown.set(client_values[0])
        self.product_dropdown.configure(values=product_values)
        self.product_dropdown.set(product_values[0])

    def _add_selected_product(self) -> None:
        products = self.repo.list_products()
        if not products:
            self._msg("Save products first")
            return
        selected = self.product_dropdown.get().split(" - ")[0]
        product = next((p for p in products if p.name == selected), None)
        if not product:
            self._msg("Product not found")
            return
        try:
            quantity = int(self.qty_entry.get().strip())
        except ValueError:
            self._msg("Quantity must be integer")
            return
        item = InvoiceItem(description=product.description or product.name, quantity=quantity, unit_price=product.unit_price)
        self.current_items.append(item)
        self._render_items()
        self._msg("Product added")

    def _render_items(self) -> None:
        self.items_box.configure(state="normal")
        self.items_box.delete("1.0", "end")
        for i, item in enumerate(self.current_items, 1):
            self.items_box.insert("end", f"{i}. {item.description} | qty {item.quantity} | unit {item.unit_price:.2f} | subtotal {item.subtotal():.2f}\n")
        self.items_box.configure(state="disabled")

    def _selected_client(self) -> Client | None:
        clients = self.repo.list_clients()
        label = self.client_dropdown.get()
        name = label.split(" (")[0]
        return next((c for c in clients if c.name == name), None)

    def _save_document(self) -> None:
        client = self._selected_client()
        if not client:
            self._msg("Select a valid client")
            return
        if not self.current_items:
            self._msg("Add at least one product")
            return
        try:
            tax_rate = Decimal(self.tax_entry.get().strip()) / Decimal("100")
            due_days = int(self.due_days_entry.get().strip())
        except (InvalidOperation, ValueError):
            self._msg("Tax and due days must be valid")
            return

        doc_type = self.doc_type_menu.get()
        number = self.repo.next_document_number(doc_type)
        document = build_document(
            number=number,
            document_type=doc_type,
            language="lv",
            client=client,
            items=self.current_items,
            tax_rate=tax_rate,
            due_date=date.today() + timedelta(days=due_days),
        )
        self.repo.add_document(document)
        self.current_items = []
        self._render_items()
        self._refresh_documents()
        self._msg(f"Document {number} saved")

    def _refresh_documents(self) -> None:
        docs = filter_and_sort_documents(
            self.repo.list_documents(),
            doc_type=self.filter_type.get(),
            search=self.search_entry.get(),
            sort_by=self.sort_menu.get(),
        )
        self.docs_box.configure(state="normal")
        self.docs_box.delete("1.0", "end")
        for d in docs:
            total = d.totals()["total"]
            self.docs_box.insert("end", f"{d.number} | {DOC_TYPE_LABELS[d.document_type]} | {d.client.name} | {d.client.country} | {d.status.upper()} | {total:.2f}\n")
        self.docs_box.configure(state="disabled")

    def _save_settings(self) -> None:
        settings = CompanySettings(
            company_name=self.set_company_name.get().strip(),
            registration_number=self.set_reg.get().strip(),
            bank=self.set_bank.get().strip(),
            swift=self.set_swift.get().strip(),
            iban=self.set_iban.get().strip(),
            logo_path=self.set_logo.get().strip(),
        )
        self.repo.save_settings(settings)
        self._msg("Settings saved")

    def _load_settings_to_form(self) -> None:
        s = self.repo.get_settings()
        self.set_company_name.insert(0, s.company_name)
        self.set_reg.insert(0, s.registration_number)
        self.set_bank.insert(0, s.bank)
        self.set_swift.insert(0, s.swift)
        self.set_iban.insert(0, s.iban)
        self.set_logo.insert(0, s.logo_path)

    def _generate_latest_pdf(self) -> None:
        docs = self.repo.list_documents()
        if not docs:
            self._msg("Save a document first")
            return
        latest = sorted(docs, key=lambda d: d.issue_date.toordinal())[-1]
        settings = self.repo.get_settings()
        output = Path("exports") / f"{latest.number}.pdf"
        try:
            generate_invoice_pdf(latest, settings, output)
            self._msg(f"PDF created: {output}")
        except Exception as exc:
            self._msg(f"PDF error: {exc}")


def run_app() -> None:
    app = BillingApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
