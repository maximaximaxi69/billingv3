from __future__ import annotations

from decimal import Decimal, InvalidOperation
import customtkinter as ctk

from .invoice import InvoiceItem, calculate_invoice_totals


class BillingApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Billing Calculator")
        self.geometry("760x520")

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.items: list[InvoiceItem] = []

        self._build_layout()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(self, text="Billing Calculator", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(18, 12))

        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="nsew")
        form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="Description").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.description_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. Monthly Plan")
        self.description_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(form_frame, text="Quantity").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.quantity_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. 2")
        self.quantity_entry.grid(row=1, column=1, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(form_frame, text="Unit Price").grid(row=2, column=0, padx=8, pady=8, sticky="w")
        self.unit_price_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. 29.99")
        self.unit_price_entry.grid(row=2, column=1, padx=8, pady=8, sticky="ew")

        add_button = ctk.CTkButton(form_frame, text="Add Item", command=self.add_item)
        add_button.grid(row=3, column=0, columnspan=2, padx=8, pady=(10, 6), sticky="ew")

        clear_button = ctk.CTkButton(form_frame, text="Clear Items", command=self.clear_items, fg_color="#7f1d1d", hover_color="#991b1b")
        clear_button.grid(row=4, column=0, columnspan=2, padx=8, pady=(6, 10), sticky="ew")

        item_frame = ctk.CTkFrame(self)
        item_frame.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="nsew")
        item_frame.grid_rowconfigure(1, weight=1)
        item_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(item_frame, text="Items", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=(10, 4), sticky="w")
        self.items_box = ctk.CTkTextbox(item_frame, height=220)
        self.items_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.items_box.configure(state="disabled")

        totals_frame = ctk.CTkFrame(self)
        totals_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        totals_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(totals_frame, text="Tax Rate (%)").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.tax_entry = ctk.CTkEntry(totals_frame, placeholder_text="e.g. 8.25")
        self.tax_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        calculate_button = ctk.CTkButton(totals_frame, text="Calculate Total", command=self.calculate_totals)
        calculate_button.grid(row=1, column=0, columnspan=2, padx=8, pady=(6, 10), sticky="ew")

        self.result_label = ctk.CTkLabel(
            totals_frame,
            text="Subtotal: $0.00\nTax: $0.00\nTotal: $0.00",
            justify="left",
            font=ctk.CTkFont(size=16),
        )
        self.result_label.grid(row=2, column=0, columnspan=2, padx=8, pady=(4, 10), sticky="w")

        self.message_label = ctk.CTkLabel(self, text="", text_color="#dc2626")
        self.message_label.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 16), sticky="w")

    def _show_error(self, message: str) -> None:
        self.message_label.configure(text=message)

    def _clear_error(self) -> None:
        self.message_label.configure(text="")

    def add_item(self) -> None:
        description = self.description_entry.get().strip() or "Item"
        try:
            quantity = int(self.quantity_entry.get().strip())
            unit_price = Decimal(self.unit_price_entry.get().strip())
        except (ValueError, InvalidOperation):
            self._show_error("Quantity must be an integer and unit price must be a number.")
            return

        try:
            item = InvoiceItem(description=description, quantity=quantity, unit_price=unit_price)
            item.subtotal()
        except ValueError as exc:
            self._show_error(str(exc))
            return

        self.items.append(item)
        self._refresh_items_box()
        self.description_entry.delete(0, "end")
        self.quantity_entry.delete(0, "end")
        self.unit_price_entry.delete(0, "end")
        self._clear_error()

    def clear_items(self) -> None:
        self.items.clear()
        self._refresh_items_box()
        self.result_label.configure(text="Subtotal: $0.00\nTax: $0.00\nTotal: $0.00")
        self._clear_error()

    def _refresh_items_box(self) -> None:
        self.items_box.configure(state="normal")
        self.items_box.delete("1.0", "end")
        for idx, item in enumerate(self.items, start=1):
            self.items_box.insert(
                "end",
                f"{idx}. {item.description} | qty: {item.quantity} | unit: ${item.unit_price:.2f} | subtotal: ${item.subtotal():.2f}\n",
            )
        self.items_box.configure(state="disabled")

    def calculate_totals(self) -> None:
        if not self.items:
            self._show_error("Add at least one item first.")
            return

        try:
            tax_percent = Decimal(self.tax_entry.get().strip())
        except InvalidOperation:
            self._show_error("Tax rate must be a valid number.")
            return

        tax_rate = tax_percent / Decimal("100")

        try:
            totals = calculate_invoice_totals(self.items, tax_rate)
        except ValueError as exc:
            self._show_error(str(exc))
            return

        self.result_label.configure(
            text=(
                f"Subtotal: ${totals['subtotal']:.2f}\n"
                f"Tax: ${totals['tax']:.2f}\n"
                f"Total: ${totals['total']:.2f}"
            )
        )
        self._clear_error()


def run_app() -> None:
    app = BillingApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
