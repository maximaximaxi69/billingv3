from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from .documents import Client, build_document
from .invoice import InvoiceItem
from .storage import BillingRepository, filter_and_sort_documents


TEXT = {
    "en": {
        "title": "Billing Desktop",
        "subtitle": "Premium invoicing workspace",
        "new_doc": "New Document",
        "documents": "Documents",
        "clients": "Clients",
        "doc_type": "Document Type",
        "client_name": "Client name",
        "reg_no": "Registration no.",
        "email": "Email",
        "address": "Address",
        "item_desc": "Item description",
        "qty": "Quantity",
        "unit": "Unit price",
        "tax": "Tax %",
        "due_days": "Due in days",
        "add_item": "Add Item",
        "save_client": "Save Client",
        "save_doc": "Save Document",
        "mark_paid": "Mark Paid",
        "refresh": "Refresh",
        "search": "Search",
        "card_invoice": "Invoice Details",
        "card_client": "Client Details",
        "card_items": "Line Items",
        "card_filter": "Filter & Sort",
        "card_clients": "Saved Clients",
    },
    "lv": {
        "title": "Rēķinu Darbvirsma",
        "subtitle": "Mūsdienīga rēķinu vide",
        "new_doc": "Jauns dokuments",
        "documents": "Dokumenti",
        "clients": "Klienti",
        "doc_type": "Dokumenta tips",
        "client_name": "Klienta nosaukums",
        "reg_no": "Reģ. nr.",
        "email": "E-pasts",
        "address": "Adrese",
        "item_desc": "Pozīcijas apraksts",
        "qty": "Daudzums",
        "unit": "Cena par vienību",
        "tax": "PVN %",
        "due_days": "Apmaksas termiņš (dienas)",
        "add_item": "Pievienot pozīciju",
        "save_client": "Saglabāt klientu",
        "save_doc": "Saglabāt dokumentu",
        "mark_paid": "Atzīmēt kā apmaksātu",
        "refresh": "Atjaunot",
        "search": "Meklēt",
        "card_invoice": "Rēķina informācija",
        "card_client": "Klienta informācija",
        "card_items": "Pozīcijas",
        "card_filter": "Filtrs un šķirošana",
        "card_clients": "Saglabātie klienti",
    },
}

DOC_TYPE_LABELS = {
    "invoice_standard": {"en": "Invoice - Standard", "lv": "Rēķins - standarta"},
    "invoice_proforma": {"en": "Invoice - Proforma", "lv": "Rēķins - proforma"},
    "invoice_recurring": {"en": "Invoice - Recurring", "lv": "Rēķins - periodiskais"},
    "delivery_note": {"en": "Delivery Note (Pavadzīme)", "lv": "Pavadzīme"},
}


class BillingApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Billing Desktop")
        self.geometry("1400x860")
        self.minsize(1200, 760)

        ctk.set_appearance_mode("dark")

        self.palette = {
            "bg": "#0e1624",
            "sidebar": "#111b2b",
            "panel": "#162236",
            "card": "#1d2b42",
            "card_alt": "#22344f",
            "text": "#e6edf8",
            "muted": "#9ab0cc",
            "accent": "#5b8cff",
            "accent_hover": "#7ba4ff",
            "danger": "#ef4444",
            "success": "#10b981",
            "border": "#2e4360",
        }

        self.configure(fg_color=self.palette["bg"])

        self.repo = BillingRepository()
        self.language = "lv"
        self.current_items: list[InvoiceItem] = []
        self.current_view = "new"

        self.font_h1 = ctk.CTkFont(family="Segoe UI", size=33, weight="bold")
        self.font_h2 = ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        self.font_body = ctk.CTkFont(family="Segoe UI", size=14)
        self.font_label = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")

        self.icons = self._load_icons()

        self._build_layout()
        self._refresh_clients()
        self._refresh_documents()

    def _load_icons(self) -> dict[str, ctk.CTkImage | None]:
        icon_dir = Path("assets") / "icons"
        icon_specs = {
            "new": "new_document.png",
            "docs": "documents.png",
            "clients": "clients.png",
            "save": "save.png",
            "mark_paid": "paid.png",
            "refresh": "refresh.png",
            "add_item": "add.png",
        }
        icons: dict[str, ctk.CTkImage | None] = {}
        for key, filename in icon_specs.items():
            path = icon_dir / filename
            if path.exists():
                image = Image.open(path)
                icons[key] = ctk.CTkImage(light_image=image, dark_image=image, size=(18, 18))
            else:
                icons[key] = None
        return icons

    def _tr(self, key: str) -> str:
        return TEXT[self.language][key]

    def _card(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent,
            fg_color=self.palette["card"],
            corner_radius=16,
            border_width=1,
            border_color=self.palette["border"],
        )
        header = ctk.CTkLabel(card, text=title, font=self.font_h2, text_color=self.palette["text"])
        header.pack(anchor="w", padx=24, pady=(18, 10))
        return card

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self,
            corner_radius=0,
            width=280,
            fg_color=self.palette["sidebar"],
            border_width=1,
            border_color=self.palette["border"],
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.sidebar,
            text=self._tr("title"),
            font=self.font_h1,
            text_color=self.palette["text"],
        )
        self.title_label.pack(padx=26, pady=(34, 4), anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text=self._tr("subtitle"),
            font=self.font_body,
            text_color=self.palette["muted"],
        )
        self.subtitle_label.pack(padx=26, pady=(0, 18), anchor="w")

        self.language_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["lv", "en"],
            command=self._set_language,
            fg_color=self.palette["card_alt"],
            button_color=self.palette["accent"],
            button_hover_color=self.palette["accent_hover"],
            dropdown_fg_color=self.palette["panel"],
        )
        self.language_menu.set(self.language)
        self.language_menu.pack(padx=24, pady=(0, 20), fill="x")

        nav_style = {
            "anchor": "w",
            "font": self.font_body,
            "corner_radius": 12,
            "height": 42,
            "fg_color": self.palette["card_alt"],
            "hover_color": self.palette["accent_hover"],
            "text_color": self.palette["text"],
        }

        self.new_btn = ctk.CTkButton(
            self.sidebar,
            text=self._tr("new_doc"),
            command=lambda: self._show_view("new"),
            image=self.icons["new"],
            **nav_style,
        )
        self.new_btn.pack(padx=24, pady=7, fill="x")

        self.docs_btn = ctk.CTkButton(
            self.sidebar,
            text=self._tr("documents"),
            command=lambda: self._show_view("docs"),
            image=self.icons["docs"],
            **nav_style,
        )
        self.docs_btn.pack(padx=24, pady=7, fill="x")

        self.clients_btn = ctk.CTkButton(
            self.sidebar,
            text=self._tr("clients"),
            command=lambda: self._show_view("clients"),
            image=self.icons["clients"],
            **nav_style,
        )
        self.clients_btn.pack(padx=24, pady=7, fill="x")

        self.message_label = ctk.CTkLabel(
            self.sidebar,
            text="",
            text_color="#f8b4b4",
            justify="left",
            wraplength=220,
            font=self.font_body,
        )
        self.message_label.pack(padx=24, pady=(30, 8), anchor="w")

        self.content = ctk.CTkFrame(self, fg_color=self.palette["panel"], corner_radius=20)
        self.content.grid(row=0, column=1, sticky="nsew", padx=24, pady=22)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.new_frame = self._build_new_document_view()
        self.docs_frame = self._build_documents_view()
        self.clients_frame = self._build_clients_view()
        self._show_view("new")

    def _build_new_document_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(frame_master := self.content, fg_color="transparent")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure((0, 1), weight=1)

        invoice_card = self._card(frame, self._tr("card_invoice"))
        invoice_card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(18, 12))
        invoice_card.grid_columnconfigure((1, 3), weight=1)

        self.doc_type_label = ctk.CTkLabel(invoice_card, text=self._tr("doc_type"), font=self.font_label, text_color=self.palette["muted"])
        self.doc_type_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.doc_type_menu = ctk.CTkOptionMenu(invoice_card, values=list(DOC_TYPE_LABELS.keys()), fg_color=self.palette["card_alt"], button_color=self.palette["accent"], button_hover_color=self.palette["accent_hover"])
        self.doc_type_menu.set("invoice_standard")
        self.doc_type_menu.grid(row=1, column=1, padx=12, pady=10, sticky="ew")

        self.tax_label = ctk.CTkLabel(invoice_card, text=self._tr("tax"), font=self.font_label, text_color=self.palette["muted"])
        self.tax_label.grid(row=1, column=2, padx=20, pady=10, sticky="w")
        self.tax_entry = ctk.CTkEntry(invoice_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.tax_entry.insert(0, "21")
        self.tax_entry.grid(row=1, column=3, padx=12, pady=10, sticky="ew")

        self.due_label = ctk.CTkLabel(invoice_card, text=self._tr("due_days"), font=self.font_label, text_color=self.palette["muted"])
        self.due_label.grid(row=2, column=2, padx=20, pady=(0, 16), sticky="w")
        self.due_days_entry = ctk.CTkEntry(invoice_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.due_days_entry.insert(0, "14")
        self.due_days_entry.grid(row=2, column=3, padx=12, pady=(0, 16), sticky="ew")

        client_card = self._card(frame, self._tr("card_client"))
        client_card.grid(row=1, column=0, sticky="nsew", padx=(18, 10), pady=(0, 14))
        client_card.grid_columnconfigure(1, weight=1)

        self.client_name_label = ctk.CTkLabel(client_card, text=self._tr("client_name"), font=self.font_label, text_color=self.palette["muted"])
        self.client_name_label.grid(row=1, column=0, padx=20, pady=9, sticky="w")
        self.client_name_entry = ctk.CTkEntry(client_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.client_name_entry.grid(row=1, column=1, padx=12, pady=9, sticky="ew")

        self.reg_label = ctk.CTkLabel(client_card, text=self._tr("reg_no"), font=self.font_label, text_color=self.palette["muted"])
        self.reg_label.grid(row=2, column=0, padx=20, pady=9, sticky="w")
        self.reg_entry = ctk.CTkEntry(client_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.reg_entry.grid(row=2, column=1, padx=12, pady=9, sticky="ew")

        self.email_label = ctk.CTkLabel(client_card, text=self._tr("email"), font=self.font_label, text_color=self.palette["muted"])
        self.email_label.grid(row=3, column=0, padx=20, pady=9, sticky="w")
        self.email_entry = ctk.CTkEntry(client_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.email_entry.grid(row=3, column=1, padx=12, pady=9, sticky="ew")

        self.address_label = ctk.CTkLabel(client_card, text=self._tr("address"), font=self.font_label, text_color=self.palette["muted"])
        self.address_label.grid(row=4, column=0, padx=20, pady=9, sticky="w")
        self.address_entry = ctk.CTkEntry(client_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.address_entry.grid(row=4, column=1, padx=12, pady=9, sticky="ew")

        self.save_client_button = ctk.CTkButton(
            client_card,
            text=self._tr("save_client"),
            command=self._save_client,
            image=self.icons["save"],
            fg_color=self.palette["accent"],
            hover_color=self.palette["accent_hover"],
            height=42,
            corner_radius=12,
        )
        self.save_client_button.grid(row=5, column=0, columnspan=2, padx=20, pady=(14, 20), sticky="ew")

        item_card = self._card(frame, self._tr("card_items"))
        item_card.grid(row=1, column=1, sticky="nsew", padx=(10, 18), pady=(0, 14))
        item_card.grid_columnconfigure(1, weight=1)
        item_card.grid_rowconfigure(5, weight=1)

        self.item_desc_label = ctk.CTkLabel(item_card, text=self._tr("item_desc"), font=self.font_label, text_color=self.palette["muted"])
        self.item_desc_label.grid(row=1, column=0, padx=20, pady=9, sticky="w")
        self.item_desc_entry = ctk.CTkEntry(item_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.item_desc_entry.grid(row=1, column=1, padx=12, pady=9, sticky="ew")

        self.qty_label = ctk.CTkLabel(item_card, text=self._tr("qty"), font=self.font_label, text_color=self.palette["muted"])
        self.qty_label.grid(row=2, column=0, padx=20, pady=9, sticky="w")
        self.qty_entry = ctk.CTkEntry(item_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.qty_entry.grid(row=2, column=1, padx=12, pady=9, sticky="ew")

        self.unit_label = ctk.CTkLabel(item_card, text=self._tr("unit"), font=self.font_label, text_color=self.palette["muted"])
        self.unit_label.grid(row=3, column=0, padx=20, pady=9, sticky="w")
        self.unit_entry = ctk.CTkEntry(item_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.unit_entry.grid(row=3, column=1, padx=12, pady=9, sticky="ew")

        self.add_item_button = ctk.CTkButton(
            item_card,
            text=self._tr("add_item"),
            command=self._add_item,
            image=self.icons["add_item"],
            fg_color=self.palette["accent"],
            hover_color=self.palette["accent_hover"],
            height=40,
            corner_radius=12,
        )
        self.add_item_button.grid(row=4, column=0, columnspan=2, padx=20, pady=(10, 12), sticky="ew")

        self.items_box = ctk.CTkTextbox(item_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"], border_width=1, corner_radius=12)
        self.items_box.grid(row=5, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="nsew")
        self.items_box.configure(state="disabled", font=self.font_body)

        self.save_doc_button = ctk.CTkButton(
            frame,
            text=self._tr("save_doc"),
            command=self._save_document,
            image=self.icons["save"],
            fg_color=self.palette["accent"],
            hover_color=self.palette["accent_hover"],
            height=48,
            corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        )
        self.save_doc_button.grid(row=2, column=0, columnspan=2, padx=18, pady=(0, 18), sticky="ew")
        return frame

    def _build_documents_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        filter_card = self._card(frame, self._tr("card_filter"))
        filter_card.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        filter_card.grid_columnconfigure((1, 3), weight=1)

        self.filter_type = ctk.CTkOptionMenu(filter_card, values=["all", *DOC_TYPE_LABELS.keys()], fg_color=self.palette["card_alt"], button_color=self.palette["accent"], button_hover_color=self.palette["accent_hover"])
        self.filter_type.set("all")
        self.filter_type.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="ew")

        self.search_entry = ctk.CTkEntry(filter_card, placeholder_text=self._tr("search"), fg_color=self.palette["card_alt"], border_color=self.palette["border"])
        self.search_entry.grid(row=1, column=1, padx=12, pady=(0, 18), sticky="ew")

        self.sort_menu = ctk.CTkOptionMenu(filter_card, values=["issue_date_desc", "issue_date_asc", "client_asc", "number_asc"], fg_color=self.palette["card_alt"], button_color=self.palette["accent"], button_hover_color=self.palette["accent_hover"])
        self.sort_menu.set("issue_date_desc")
        self.sort_menu.grid(row=1, column=2, padx=12, pady=(0, 18), sticky="ew")

        self.refresh_button = ctk.CTkButton(filter_card, text=self._tr("refresh"), command=self._refresh_documents, image=self.icons["refresh"], fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], corner_radius=12, height=40)
        self.refresh_button.grid(row=1, column=3, padx=18, pady=(0, 18), sticky="ew")

        self.docs_box = ctk.CTkTextbox(frame, fg_color=self.palette["card"], border_color=self.palette["border"], border_width=1, corner_radius=14)
        self.docs_box.grid(row=1, column=0, padx=18, pady=8, sticky="nsew")
        self.docs_box.configure(state="disabled", font=self.font_body)

        bottom = ctk.CTkFrame(frame, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=18, pady=(4, 18))
        bottom.grid_columnconfigure(0, weight=1)

        self.mark_paid_entry = ctk.CTkEntry(bottom, placeholder_text="INV-00001 / PRO-00001 / PAV-00001", fg_color=self.palette["card"], border_color=self.palette["border"])
        self.mark_paid_entry.grid(row=0, column=0, padx=(0, 12), pady=0, sticky="ew")
        self.mark_paid_button = ctk.CTkButton(bottom, text=self._tr("mark_paid"), command=self._mark_paid, image=self.icons["mark_paid"], fg_color=self.palette["success"], hover_color="#34d399", corner_radius=12, height=40)
        self.mark_paid_button.grid(row=0, column=1, sticky="ew")
        return frame

    def _build_clients_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        client_card = self._card(frame, self._tr("card_clients"))
        client_card.grid(row=0, column=0, padx=18, pady=18, sticky="nsew")
        client_card.grid_rowconfigure(1, weight=1)
        client_card.grid_columnconfigure(0, weight=1)

        self.clients_box = ctk.CTkTextbox(client_card, fg_color=self.palette["card_alt"], border_color=self.palette["border"], border_width=1, corner_radius=12)
        self.clients_box.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.clients_box.configure(state="disabled", font=self.font_body)
        return frame

    def _show_view(self, view: str) -> None:
        self.current_view = view
        for frame in (self.new_frame, self.docs_frame, self.clients_frame):
            frame.grid_forget()
        if view == "new":
            self.new_frame.grid(row=0, column=0, sticky="nsew")
        elif view == "docs":
            self.docs_frame.grid(row=0, column=0, sticky="nsew")
            self._refresh_documents()
        else:
            self.clients_frame.grid(row=0, column=0, sticky="nsew")
            self._refresh_clients()

    def _set_language(self, lang: str) -> None:
        self.language = lang
        self._apply_translations()

    def _apply_translations(self) -> None:
        self.title_label.configure(text=self._tr("title"))
        self.subtitle_label.configure(text=self._tr("subtitle"))
        self.new_btn.configure(text=self._tr("new_doc"))
        self.docs_btn.configure(text=self._tr("documents"))
        self.clients_btn.configure(text=self._tr("clients"))
        self.doc_type_label.configure(text=self._tr("doc_type"))
        self.tax_label.configure(text=self._tr("tax"))
        self.due_label.configure(text=self._tr("due_days"))
        self.client_name_label.configure(text=self._tr("client_name"))
        self.reg_label.configure(text=self._tr("reg_no"))
        self.email_label.configure(text=self._tr("email"))
        self.address_label.configure(text=self._tr("address"))
        self.item_desc_label.configure(text=self._tr("item_desc"))
        self.qty_label.configure(text=self._tr("qty"))
        self.unit_label.configure(text=self._tr("unit"))
        self.add_item_button.configure(text=self._tr("add_item"))
        self.save_client_button.configure(text=self._tr("save_client"))
        self.save_doc_button.configure(text=self._tr("save_doc"))
        self.refresh_button.configure(text=self._tr("refresh"))
        self.search_entry.configure(placeholder_text=self._tr("search"))
        self.mark_paid_button.configure(text=self._tr("mark_paid"))

    def _message(self, text: str) -> None:
        self.message_label.configure(text=text)

    def _save_client(self) -> None:
        client = Client(
            name=self.client_name_entry.get().strip(),
            registration_number=self.reg_entry.get().strip(),
            email=self.email_entry.get().strip(),
            address=self.address_entry.get().strip(),
        )
        if not client.name or not client.registration_number:
            self._message("Client name and registration number are required.")
            return
        self.repo.add_or_update_client(client)
        self._refresh_clients()
        self._message("Client saved.")

    def _add_item(self) -> None:
        try:
            item = InvoiceItem(
                description=self.item_desc_entry.get().strip() or "Item",
                quantity=int(self.qty_entry.get().strip()),
                unit_price=Decimal(self.unit_entry.get().strip()),
            )
            item.subtotal()
        except (ValueError, InvalidOperation) as exc:
            self._message(f"Invalid item: {exc}")
            return
        self.current_items.append(item)
        self.item_desc_entry.delete(0, "end")
        self.qty_entry.delete(0, "end")
        self.unit_entry.delete(0, "end")
        self._refresh_items_box()
        self._message("Item added.")

    def _refresh_items_box(self) -> None:
        self.items_box.configure(state="normal")
        self.items_box.delete("1.0", "end")
        for idx, item in enumerate(self.current_items, start=1):
            self.items_box.insert("end", f"{idx}. {item.description}  •  x{item.quantity}  •  {item.unit_price:.2f}  =  {item.subtotal():.2f}\n")
        self.items_box.configure(state="disabled")

    def _save_document(self) -> None:
        if not self.current_items:
            self._message("Add at least one item first.")
            return

        client = Client(
            name=self.client_name_entry.get().strip(),
            registration_number=self.reg_entry.get().strip(),
            email=self.email_entry.get().strip(),
            address=self.address_entry.get().strip(),
        )
        if not client.name or not client.registration_number:
            self._message("Client name and registration number are required.")
            return

        try:
            tax_rate = Decimal(self.tax_entry.get().strip()) / Decimal("100")
            due_days = int(self.due_days_entry.get().strip())
        except (InvalidOperation, ValueError):
            self._message("Tax and due days must be valid numbers.")
            return

        doc_type = self.doc_type_menu.get()
        number = self.repo.next_document_number(doc_type)

        try:
            document = build_document(
                number=number,
                document_type=doc_type,
                language=self.language,
                client=client,
                items=self.current_items,
                tax_rate=tax_rate,
                due_date=date.today() + timedelta(days=due_days),
            )
        except ValueError as exc:
            self._message(str(exc))
            return

        self.repo.add_document(document)
        totals = document.totals()
        self.current_items = []
        self._refresh_items_box()
        self._refresh_documents()
        self._message(f"Saved {number}. Total: {totals['total']:.2f}")

    def _refresh_documents(self) -> None:
        docs = self.repo.list_documents()
        filtered = filter_and_sort_documents(
            docs,
            doc_type=self.filter_type.get(),
            search=self.search_entry.get(),
            sort_by=self.sort_menu.get(),
        )

        self.docs_box.configure(state="normal")
        self.docs_box.delete("1.0", "end")
        for doc in filtered:
            totals = doc.totals()
            label = DOC_TYPE_LABELS[doc.document_type][doc.language]
            self.docs_box.insert(
                "end",
                f"{doc.number}  |  {label}  |  {doc.client.name}  |  {doc.issue_date}  |  {doc.status.upper()}  |  {totals['total']:.2f}\n",
            )
        self.docs_box.configure(state="disabled")

    def _mark_paid(self) -> None:
        number = self.mark_paid_entry.get().strip()
        if not number:
            self._message("Enter a document number.")
            return
        if self.repo.mark_document_paid(number):
            self._refresh_documents()
            self._message(f"{number} marked paid.")
        else:
            self._message("Document not found.")

    def _refresh_clients(self) -> None:
        clients = self.repo.list_clients()
        self.clients_box.configure(state="normal")
        self.clients_box.delete("1.0", "end")
        for client in clients:
            self.clients_box.insert("end", f"{client.name}  |  {client.registration_number}  |  {client.email}  |  {client.address}\n")
        self.clients_box.configure(state="disabled")


def run_app() -> None:
    app = BillingApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
