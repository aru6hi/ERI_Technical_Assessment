'''Python tools for totals and invoice generation.'''

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from langchain_core.tools import tool
from openpyxl import Workbook
from openpyxl.styles import Font

from .data import EnergyData, EnergyDataError

TARIFF = Decimal("0.25")


def make_tools(data: EnergyData, output_dir: Path):
    @tool
    def calculate_total(start_date: str, end_date: str) -> str:
        '''Calculate kWh for a date range. Use YYYY-MM-DD dates.'''
        try:
            total = data.total(start_date, end_date)
            return json.dumps({
                "action": "total", "start": start_date, "end": end_date,
                "kwh": str(total.total_kwh),
            })
        except EnergyDataError as exc:
            return json.dumps({"error": str(exc)})

    @tool
    def generate_invoice(start_date: str, end_date: str) -> str:
        '''Create an Excel invoice for an inclusive date range. Use YYYY-MM-DD dates.'''
        try:
            total = data.total(start_date, end_date)
        except EnergyDataError as exc:
            return json.dumps({"error": str(exc)})

        amount = (total.total_kwh * TARIFF).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"energy_invoice_{start_date}_{end_date}"
        path, suffix = output_dir / f"{stem}.xlsx", 2
        while path.exists():
            path, suffix = output_dir / f"{stem}_{suffix}.xlsx", suffix + 1

        workbook = Workbook() #Generate an excel invoice
        sheet = workbook.active
        sheet.title = "Invoice"
        rows = [
            ("Energy invoice", None),
            ("Billing period start", total.start_date),
            ("Billing period end", total.end_date),
            ("Total energy consumption (kWh)", float(total.total_kwh)),
            ("Energy tariff (SGD/kWh)", float(TARIFF)),
            ("Total amount payable (SGD)", float(amount)),
        ]
        for row, values in enumerate(rows, start=1):
            sheet.cell(row, 1, values[0])
            if values[1] is not None:
                sheet.cell(row, 2, values[1])
        sheet["A1"].font = sheet["A6"].font = sheet["B6"].font = Font(bold=True)
        sheet.column_dimensions["A"].width = 38
        sheet.column_dimensions["B"].width = 20
        sheet["B2"].number_format = sheet["B3"].number_format = "dd mmm yyyy"
        sheet["B4"].number_format = "#,##0.00"
        sheet["B5"].number_format = sheet["B6"].number_format = '"SGD "0.00'
        workbook.save(path)
        return json.dumps({
            "action": "invoice", "start": start_date, "end": end_date,
            "kwh": str(total.total_kwh), "tariff": str(TARIFF),
            "amount": str(amount), "file": str(path.resolve()),
        })

    return [calculate_total, generate_invoice]
