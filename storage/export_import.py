from datetime import datetime
from io import BytesIO
import pandas as pd


class ExportImport:
    """Utility untuk export-import data dari list dictionary."""

    @staticmethod
    def to_dataframe(records: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(records)

    @staticmethod
    def to_csv_bytes(records: list[dict]) -> bytes:
        df = ExportImport.to_dataframe(records)
        return df.to_csv(index=False).encode("utf-8")

    @staticmethod
    def to_excel_bytes(records: list[dict], sheet_name: str = "Data") -> bytes:
        df = ExportImport.to_dataframe(records)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        return buffer.getvalue()

    @staticmethod
    def to_pdf_bytes(records: list[dict], title: str = "Laporan SIPERU") -> bytes:
        lines = ExportImport._records_to_report_lines(records, title)
        return ExportImport._plain_text_pdf(lines)

    @staticmethod
    def _records_to_report_lines(records: list[dict], title: str) -> list[str]:
        lines = [
            title,
            f"Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total data: {len(records)}",
            "",
        ]

        if not records:
            lines.append("Belum ada data untuk laporan ini.")
            return lines

        df = ExportImport.to_dataframe(records).fillna("")
        columns = [str(column) for column in df.columns]
        available_chars = 138
        separator_width = 3 * (len(columns) - 1)
        max_width = 24
        min_width = 6

        widths = []
        for column in columns:
            values = [str(value).replace("\n", " ") for value in df[column].head(200)]
            longest_value = max([len(column), *(len(value) for value in values)])
            widths.append(min(max(longest_value, min_width), max_width))

        while sum(widths) + separator_width > available_chars and any(width > min_width for width in widths):
            largest_index = max(range(len(widths)), key=lambda index: widths[index])
            widths[largest_index] -= 1

        header = " | ".join(ExportImport._fit_text(column, width) for column, width in zip(columns, widths))
        divider = "-+-".join("-" * width for width in widths)
        lines.extend([header, divider])

        for _, row in df.iterrows():
            line = " | ".join(
                ExportImport._fit_text(row[column], width)
                for column, width in zip(df.columns, widths)
            )
            lines.append(line)

        return lines

    @staticmethod
    def _fit_text(value, width: int) -> str:
        text = str(value).replace("\r", " ").replace("\n", " ")
        if len(text) > width:
            return text[: max(width - 3, 0)] + "..."[: min(3, width)]
        return text.ljust(width)

    @staticmethod
    def _plain_text_pdf(lines: list[str]) -> bytes:
        page_width = 842
        page_height = 595
        margin_x = 36
        margin_y = 36
        font_size = 9
        leading = 12
        max_lines_per_page = int((page_height - (margin_y * 2)) / leading)
        pages = [
            lines[index : index + max_lines_per_page]
            for index in range(0, len(lines), max_lines_per_page)
        ] or [["Belum ada data."]]

        objects: list[bytes] = []
        catalog_id = 1
        pages_id = 2
        font_id = 3
        page_ids = []

        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objects.append(b"")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

        for page_lines in pages:
            page_id = len(objects) + 1
            content_id = page_id + 1
            page_ids.append(page_id)

            content = ExportImport._pdf_page_content(
                page_lines,
                margin_x,
                page_height - margin_y,
                font_size,
                leading,
            )
            objects.append(
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {page_width} {page_height}] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode("latin-1")
            )
            objects.append(
                b"<< /Length " + str(len(content)).encode("latin-1") + b" >>\nstream\n" + content + b"\nendstream"
            )

        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("latin-1")

        return ExportImport._build_pdf(objects, catalog_id)

    @staticmethod
    def _pdf_page_content(lines: list[str], x: int, y: int, font_size: int, leading: int) -> bytes:
        commands = [
            "BT",
            f"/F1 {font_size} Tf",
            f"{leading} TL",
            f"1 0 0 1 {x} {y} Tm",
        ]
        for index, line in enumerate(lines):
            if index > 0:
                commands.append("T*")
            commands.append(f"({ExportImport._pdf_escape(line)}) Tj")
        commands.append("ET")
        return "\n".join(commands).encode("latin-1", errors="replace")

    @staticmethod
    def _pdf_escape(value: str) -> str:
        return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    @staticmethod
    def _build_pdf(objects: list[bytes], catalog_id: int) -> bytes:
        output = BytesIO()
        output.write(b"%PDF-1.4\n")
        offsets = [0]

        for object_id, body in enumerate(objects, start=1):
            offsets.append(output.tell())
            output.write(f"{object_id} 0 obj\n".encode("latin-1"))
            output.write(body)
            output.write(b"\nendobj\n")

        xref_position = output.tell()
        output.write(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        output.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            output.write(f"{offset:010d} 00000 n \n".encode("latin-1"))

        output.write(
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_position}\n%%EOF".encode("latin-1")
        )
        return output.getvalue()

    @staticmethod
    def read_uploaded_file(uploaded_file) -> list[dict]:
        if uploaded_file is None:
            return []
        filename = uploaded_file.name.lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("Format file harus CSV atau Excel (.xlsx/.xls).")
        df = df.fillna("")
        return df.to_dict(orient="records")
