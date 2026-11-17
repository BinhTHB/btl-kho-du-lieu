# -*- coding: utf-8 -*-
"""Kiểm tra trực tiếp file DOCX vừa sinh: nội dung, encoding, ảnh, số trang."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "Bao_cao_BTL_Kho_du_lieu_Nhom9.docx"
HINH = Path(__file__).resolve().parent / "hinh"

FORBIDDEN = [
    "SQLite", "sqlite", "Airflow", "airflow", "Flask", "SQLAlchemy",
    "vòng lặp nền", "1,2 giây", "1.2 giây", "chạy ngầm", "PostgreSQL",
    "Materialized View", "GPA", "SinhVien", "KetQua", "TaiKhoan",
    "开始", "avec ", "Equinox", "Flask", "ORM",
]
REQUIRED = [
    "OLTP_QuanLyHocTap", "DW_QuanLyHocTap", "Trusted_Connection", "localhost",
    "Dagster", "*/2 * * * *", "step_extract", "step_quality_gate", "step_scd2",
    "step_load_facts", "step_audit", "oltp_extracted_batch", "dw_audit_and_summary",
    "Seed 9", "344", "822", "51", "109", "6,72", "13 197",
    "B23DCKD004", "B23DCKD008", "B23DCKD014", "B23DCKD030",
    "hoc_sinh_key", "49", "D23CQCN01", "D23CQKD03", "110,5", "552,8", "35 = 5 × 7",
    "iv_diem_theo_mon_thang", "iv_chuyen_can_theo_lop_tuan", "WITH (NOEXPAND)",
    "SCHEMABINDING", "vw_drill_across", "etl_reject", "Nguồn = Nạp + Loại",
    "/hoc-tap", "/bi", "HocTapOLAP", "Excel PivotTable", "SSDT", "ODBC Driver 17",
    "50%", "30%", "20%", "Execution Plan", "STATISTICS IO", "31 ca",
]

fails: list[str] = []
warns: list[str] = []


def check(ok: bool, message: str) -> None:
    print(("  [OK]   " if ok else "  [LOI]  ") + message)
    if not ok:
        fails.append(message)


def main() -> int:
    if not DOCX.exists():
        print("Không thấy file:", DOCX)
        return 1
    doc = Document(str(DOCX))

    # 1. Gom toàn bộ văn bản (đoạn + ô bảng + header/footer)
    parts: list[str] = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    for section in doc.sections:
        parts += [p.text for p in section.header.paragraphs]
        parts += [p.text for p in section.footer.paragraphs]
    full = "\n".join(parts)

    print("\n=== 1. TỪ KHÓA CŨ (phải không còn) ===")
    for word in FORBIDDEN:
        check(word not in full, f"Không chứa '{word}'")

    print("\n=== 2. TỪ KHÓA BẮT BUỘC (phải có) ===")
    for word in REQUIRED:
        check(word in full, f"Có '{word}'")

    print("\n=== 3. ENCODING TIẾNG VIỆT ===")
    check("\ufffd" not in full, "Không có ký tự thay thế encoding (U+FFFD)")
    for marker in ("Ã", "â€", "Ä", "Æ"):
        check(marker not in full, f"Không có chuỗi mojibake '{marker}'")
    check("HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG" in full, "Có tên học viện tiếng Việt")
    check("Nguyễn Quý Tường Anh" in full and "Mai Quốc Hưng" in full, "Có đủ tên thành viên")

    print("\n=== 4. CẤU TRÚC / MỤC TRỐNG ===")
    paragraphs = doc.paragraphs
    headings = []
    for i, p in enumerate(paragraphs):
        if p.style.name.startswith("Heading") and p.text.strip():
            level = int(p.style.name.split()[-1]) if p.style.name.split()[-1].isdigit() else 1
            headings.append((i, level, p.text.strip()))
    empty = []
    for idx, (i, level, text) in enumerate(headings):
        # Phạm vi của một đề mục = đến đề mục kế tiếp có cấp <= cấp hiện tại
        nxt = len(paragraphs)
        for j, lev2, _ in headings[idx + 1:]:
            if lev2 <= level:
                nxt = j
                break
        between = [q.text.strip() for q in paragraphs[i + 1:nxt] if q.text.strip()]
        if not between:
            empty.append(text[:60])
    check(not empty, "Không có đề mục trống" + (f" (rỗng: {empty})" if empty else ""))
    check(len(doc.tables) >= 15, f"Số bảng >= 15 (thực tế {len(doc.tables)})")
    check(len(paragraphs) >= 200, f"Số đoạn >= 200 (thực tế {len(paragraphs)})")

    with zipfile.ZipFile(DOCX) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        settings_xml = z.read("word/settings.xml").decode("utf-8")
    check('TOC \\o "1-3"' in xml or "TOC \\o" in xml, "Có trường Mục lục tự động (TOC)")
    check("updateFields" in settings_xml, "Tự cập nhật trường khi mở")

    print("\n=== 5. ẢNH NHÚNG ===")
    media = [n for n in zipfile.ZipFile(DOCX).namelist() if n.startswith("word/media/")]
    check(len(media) >= 8, f"Số ảnh nhúng >= 8 (thực tế {len(media)})")
    check("Bảng điều khiển trên cổng /bi" in full and "Hình 3.2" in full, "Có ảnh dashboard /bi")
    check("Hình 4.3" in full and "vw_drill_across" in full, "Có ảnh drill-across SSMS")
    for name in ["ssms_03_danh_sach_database.png", "hinh_4_2_ssms_query.png",
                 "excel_01_rollup.png", "vs_06_dsv_full.png"]:
        check((HINH / name).is_file(), f"File ảnh nguồn tồn tại: {name}")

    print("\n=== 6. SỐ TRANG (Word COM, cập nhật TOC rồi đếm) ===")
    pages = -1
    try:
        import pythoncom
        import win32com.client as win32
        pdf = Path(__file__).resolve().parent / "Bao_cao_BTL_Kho_du_lieu_Nhom9.pdf"
        pythoncom.CoInitialize()
        app = win32.DispatchEx("Word.Application")
        app.Visible = False
        app.DisplayAlerts = 0
        try:
            d = app.Documents.Open(str(DOCX))
            d.Fields.Update()
            d.Repaginate()
            pages = d.ComputeStatistics(2)  # wdStatisticPages
            d.Save()
            d.SaveAs(str(pdf), FileFormat=17)
            d.Close(True)
        finally:
            app.Quit()
        check(0 < pages <= 30, f"Số trang <= 30 (thực tế {pages})")
        print(f"     Đã xuất thử PDF để đếm: {pdf}")
    except Exception as exc:  # Word COM có thể không có trên máy khác
        warns.append(f"Không đếm được số trang bằng Word: {exc}")
        print("  [WARN] Không đếm được số trang bằng Word:", exc)

    print("\n=== TỔNG KẾT ===")
    if fails:
        print(f"KHONG DAT: {len(fails)} loi")
        for f in fails:
            print("  -", f)
        return 1
    print(f"DAT: tat ca kiem tra dung so. So trang = {pages}.")
    for w in warns:
        print("  Luu y:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
