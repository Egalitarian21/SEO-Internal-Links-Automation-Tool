from datetime import datetime

from app.errors import AppError
from app.schemas import ReportRequest, ReportResult
from app.services.storage import StorageService
from app.utils.slug import sanitize_customer_name, slugify_text, slugify_url


class ExcelReporterService:
    HEADERS = [
        "#",
        "Source Blog URL",
        "Source Blog Title",
        "Anchor Text",
        "Target URL",
        "Target Title",
        "Insert Paragraph",
    ]

    def __init__(self, storage: StorageService | None = None) -> None:
        self.storage = storage or StorageService()

    def _set_column_width(self, ws) -> None:
        limits = {"D": 60, "G": 60}
        for col in "ABCDEFG":
            max_len = 10
            for cell in ws[col]:
                value = str(cell.value) if cell.value is not None else ""
                max_len = max(max_len, len(value))
            ws.column_dimensions[col].width = min(max_len + 2, limits.get(col, 50))

    def write(self, request: ReportRequest) -> ReportResult:
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill
        except Exception as exc:  # pragma: no cover
            raise AppError("EXCEL_WRITE_FAILED", "openpyxl is required to generate Excel output.") from exc

        customer = sanitize_customer_name(request.customer)
        self.storage.ensure_customer_dirs(customer)

        result = request.recommend_result
        blog_slug_source = result.blog_title or request.blog_url
        blog_slug = slugify_text(blog_slug_source, max_len=80) if result.blog_title else slugify_url(request.blog_url)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        excel_path = self.storage.get_excel_report_path(customer, blog_slug, timestamp)

        wb = Workbook()
        ws = wb.active
        ws.title = "Recommendations"
        ws.append(self.HEADERS)

        header_fill = PatternFill(fill_type="solid", start_color="E5E7EB", end_color="E5E7EB")
        for idx, _ in enumerate(self.HEADERS, start=1):
            cell = ws.cell(row=1, column=idx)
            cell.font = Font(bold=True)
            cell.fill = header_fill

        for row_num, rec in enumerate(result.recommendations, start=1):
            ws.append(
                [
                    row_num,
                    result.blog_url,
                    result.blog_title or "",
                    rec.anchor_text,
                    rec.target_url,
                    rec.target_title,
                    rec.insert_paragraph,
                ]
            )
            ws.cell(row=row_num + 1, column=4).font = Font(bold=True)

        self._set_column_width(ws)

        meta = wb.create_sheet(title="Metadata")
        metadata = [
            ("Customer", customer),
            ("Source Blog URL", result.blog_url),
            ("Total Recommendations", len(result.recommendations)),
            ("Score Threshold", request.recommend_result.recommendations[0].relevance_score if result.recommendations else ""),
            ("Wiki Cards Library Size", result.library_size),
            ("Cards Filtered (Stage 1)", result.candidates_filtered),
        ]
        meta.append(["Key", "Value"])
        for cell in meta[1]:
            cell.font = Font(bold=True)
            cell.fill = header_fill
        for key, value in metadata:
            meta.append([key, value])
        meta.column_dimensions["A"].width = 28
        meta.column_dimensions["B"].width = 48

        try:
            excel_path.parent.mkdir(parents=True, exist_ok=True)
            wb.save(excel_path)
        except Exception as exc:
            raise AppError("EXCEL_WRITE_FAILED", str(exc)) from exc

        return ReportResult(
            customer=customer,
            blog_url=result.blog_url,
            excel_path=str(excel_path.resolve()),
            file_name=excel_path.name,
            rows_written=len(result.recommendations),
            file_size_bytes=excel_path.stat().st_size,
            generated_at=datetime.now(),
        )
