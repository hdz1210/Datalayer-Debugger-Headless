"""
Excel Report Exporter for DataLayer Audit.
Exports trigger actions, button names, and full DataLayer payloads to .xlsx.
Pure English schema, styling, and annotations.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Union, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


class DataLayerExcelExporter:
    """Handles professional Excel export for autonomous DataLayer audit records."""

    HEADERS = [
        {"col": "A", "key": "index", "name": "Index", "width": 10, "align": "center"},
        {"col": "B", "key": "link_trigger", "name": "Link Trigger", "width": 42, "align": "left"},
        {"col": "C", "key": "button_name", "name": "Button Name", "width": 35, "align": "left"},
        {"col": "D", "key": "ga4_event", "name": "GA4 Event", "width": 22, "align": "center"},
        {"col": "E", "key": "datalayer", "name": "DataLayer Payload", "width": 75, "align": "left"},
        {"col": "F", "key": "status", "name": "Status / Audit Notes", "width": 38, "align": "left"},
    ]

    def __init__(self, target_domain: str = "Website"):
        self.target_domain = target_domain
        self.records: List[Dict[str, Any]] = []

    def add_record(
        self,
        link_trigger: str,
        button_name: str,
        datalayer_payload: Union[dict, list, str, None],
        ga4_event: str = "",
        status: str = "PASS"
    ) -> None:
        """Add an audit row record to the internal buffer."""
        record_idx = len(self.records) + 1

        # Pretty print DataLayer JSON with 2-space indentation
        if isinstance(datalayer_payload, (dict, list)):
            try:
                formatted_dl = json.dumps(datalayer_payload, indent=2, ensure_ascii=False)
            except Exception:
                formatted_dl = str(datalayer_payload)
        elif isinstance(datalayer_payload, str):
            formatted_dl = datalayer_payload
        else:
            formatted_dl = "{}"

        # Auto-extract ga4_event name if not explicitly provided
        if not ga4_event and isinstance(datalayer_payload, dict):
            ga4_event = str(datalayer_payload.get("event", ""))

        self.records.append({
            "index": record_idx,
            "link_trigger": link_trigger,
            "button_name": button_name,
            "ga4_event": ga4_event or "(None)",
            "datalayer": formatted_dl,
            "status": status
        })

    def export(self, output_dir: str = ".", custom_filename: Optional[str] = None) -> str:
        """Export all recorded triggers to a styled Excel (.xlsx) file."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_domain = "".join(c if c.isalnum() else "_" for c in self.target_domain).strip("_")
        filename = custom_filename or f"DataLayer_Audit_{sanitized_domain}_{timestamp}.xlsx"
        file_path = os.path.join(output_dir, filename)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "DataLayer_Audit_Triggers"
        ws.views.sheetView[0].showGridLines = True

        # Typography and Colors
        font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")  # Slate 800

        font_text = Font(name="Segoe UI", size=10)
        font_button = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
        font_code = Font(name="Consolas", size=9, color="0F172A")
        font_event = Font(name="Segoe UI Semibold", size=10, color="0D9488")  # Teal 600

        fill_pass = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")  # Emerald 100
        fill_warn = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")  # Amber 100
        fill_fail = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")  # Rose 100

        thin_side = Side(border_style="thin", color="CBD5E1")
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        # 1. Write Header Row
        ws.row_dimensions[1].height = 28
        for col_idx, h in enumerate(self.HEADERS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=h["name"])
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = cell_border
            ws.column_dimensions[h["col"]].width = h["width"]

        # 2. Write Data Rows
        for row_idx, r in enumerate(self.records, start=2):
            # Index
            c_idx = ws.cell(row=row_idx, column=1, value=r["index"])
            c_idx.alignment = Alignment(horizontal="center", vertical="top")
            c_idx.font = font_text
            c_idx.border = cell_border

            # Link Trigger
            c_link = ws.cell(row=row_idx, column=2, value=r["link_trigger"])
            c_link.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            c_link.font = font_text
            c_link.border = cell_border

            # Button Name
            c_btn = ws.cell(row=row_idx, column=3, value=r["button_name"])
            c_btn.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            c_btn.font = font_button
            c_btn.border = cell_border

            # GA4 Event
            c_evt = ws.cell(row=row_idx, column=4, value=r["ga4_event"])
            c_evt.alignment = Alignment(horizontal="center", vertical="top")
            c_evt.font = font_event
            c_evt.border = cell_border

            # DataLayer Payload (Full JSON formatted with Wrap Text)
            c_dl = ws.cell(row=row_idx, column=5, value=r["datalayer"])
            c_dl.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            c_dl.font = font_code
            c_dl.border = cell_border

            # Status / Audit Notes
            c_stat = ws.cell(row=row_idx, column=6, value=r["status"])
            c_stat.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            c_stat.font = font_text
            c_stat.border = cell_border

            # Conditional Status Background Tint
            stat_upper = str(r["status"]).upper()
            if "PASS" in stat_upper:
                c_stat.fill = fill_pass
            elif "WARN" in stat_upper:
                c_stat.fill = fill_warn
            elif "FAIL" in stat_upper or "ERROR" in stat_upper:
                c_stat.fill = fill_fail

        # Enable Auto-Filter on table header
        last_col = get_column_letter(len(self.HEADERS))
        last_row = max(len(self.records) + 1, 1)
        ws.auto_filter.ref = f"A1:{last_col}{last_row}"

        wb.save(file_path)
        return os.path.abspath(file_path)
