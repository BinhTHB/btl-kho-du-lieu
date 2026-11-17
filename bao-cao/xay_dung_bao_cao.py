# -*- coding: utf-8 -*-
"""Sinh báo cáo BTL Kho dữ liệu (Nhóm 9) từ khung mẫu PTIT.

Nguyên tắc:
- Không tạo file Word trắng: luôn sao chép ``Mẫu Tiểu luận_DW.docx`` rồi ghi nội dung.
- Tự sao lưu bản cũ vào ``back-up-docx/`` trước khi ghi đè.
- Toàn bộ nội dung thân bài được khai báo trong ``BLOCKS``; danh mục bảng/hình
  được sinh ra từ cùng một nguồn dữ liệu đó (không hardcode danh mục).
"""

from __future__ import annotations

import re
import shutil
import sys
import zipfile
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = Path(r"C:\Users\ADMIN\.agents\skills\ptit-academic-writing\scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))
from docx_tools import backup_docx  # noqa: E402

TEMPLATE = Path(r"E:\Hoc-Tap\Kho Dữ Liệu\Tài liệu học tập\Mẫu Tiểu luận_DW.docx")
DEST = ROOT / "Bao_cao_BTL_Kho_du_lieu_Nhom9.docx"
HINH = Path(__file__).resolve().parent / "hinh"
SO_DO = Path(__file__).resolve().parent / "so-do"

# ---------------------------------------------------------------------------
# Thông tin chung / bìa / phiếu phân công
# ---------------------------------------------------------------------------
GVHD = "ThS. Nguyễn Thị Thu Hiên"
TEN_DE_TAI = "HỆ THỐNG QUẢN LÝ HỌC TẬP VÀ ÔN LUYỆN TRỰC TUYẾN"
LOP = "D23CQKD02-B – Nhóm 9 (lớp học phần Nhóm 2)"
THANH_VIEN = [
    ("Nguyễn Quý Tường Anh", "B23DCKD004", "Kiến trúc kho, SCD và ETL",
     "Thiết kế Fact Constellation, cài đặt SCD Type 2, xây dựng năm bước ETL và cổng chất lượng."),
    ("Tạ Hoà Bình", "B23DCKD008", "SQL Server và SSAS",
     "Triển khai hai CSDL trên SQL Server, indexed view, khối SSAS và hướng dẫn Excel PivotTable."),
    ("Nguyễn Tiến Đạt", "B23DCKD014", "OLTP và giao diện",
     "Tám bảng OLTP 3NF, bộ sinh dữ liệu mẫu và hai cổng web /hoc-tap, /bi."),
    ("Mai Quốc Hưng", "B23DCKD030", "Tầng tổng hợp và báo cáo",
     "Truy vấn đối soát drill-across, đo indexed view, kiểm thử và biên soạn báo cáo."),
]
DIEM_THANH_VIEN = ["Tường Anh", "Hoà Bình", "Tiến Đạt", "Quốc Hưng"]

ABBREVIATIONS = [
    ["OLTP", "Online Transaction Processing", "Xử lý giao dịch tác nghiệp"],
    ["OLAP", "Online Analytical Processing", "Xử lý phân tích trực tuyến"],
    ["ETL", "Extract, Transform, Load", "Trích xuất, biến đổi và nạp"],
    ["DW", "Data Warehouse", "Kho dữ liệu"],
    ["SCD", "Slowly Changing Dimension", "Chiều biến đổi chậm"],
    ["3NF", "Third Normal Form", "Dạng chuẩn ba"],
    ["SSMS", "SQL Server Management Studio", "Công cụ quản trị SQL Server"],
    ["SSAS", "SQL Server Analysis Services", "Dịch vụ phân tích của SQL Server"],
    ["SSDT", "SQL Server Data Tools", "Công cụ dự án đa chiều trong Visual Studio"],
    ["DSV", "Data Source View", "Góc nhìn nguồn dữ liệu của khối SSAS"],
]

REFERENCES = [
    "[1] W. H. Inmon, Building the Data Warehouse, 4th ed. Indianapolis, IN, USA: Wiley, 2005.",
    "[2] R. Kimball and M. Ross, The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling, 3rd ed. Indianapolis, IN, USA: Wiley, 2013.",
    '[3] E. F. Codd, S. B. Codd, and C. T. Salley, "Providing OLAP to user-analysts: An IT mandate," E.F. Codd & Associates, 1993.',
    "[4] R. Kimball and J. Caserta, The Data Warehouse ETL Toolkit. Indianapolis, IN, USA: Wiley, 2004.",
    '[5] Microsoft, "Trusted connection and ODBC Driver for SQL Server," SQL Server documentation. [Online]. Available: https://learn.microsoft.com/en-us/sql/connect/odbc/windows/microsoft-odbc-driver-for-sql-server. (Truy cập: 16/11/2026).',
    '[6] "Dagster – an orchestrator for data assets," Dagster documentation. [Online]. Available: https://docs.dagster.io/. (Truy cập: 16/11/2026).',
    '[7] "FastAPI documentation," 2026. [Online]. Available: https://fastapi.tiangolo.com/. (Truy cập: 16/11/2026).',
    '[8] Microsoft, "Create indexed views," SQL Server documentation. [Online]. Available: https://learn.microsoft.com/en-us/sql/relational-databases/views/create-indexed-views. (Truy cập: 16/11/2026).',
    '[9] Microsoft, "Multidimensional model databases (SSAS)," Analysis Services documentation. [Online]. Available: https://learn.microsoft.com/en-us/analysis-services/multidimensional-models/multidimensional-model-databases-ssas. (Truy cập: 16/11/2026).',
    '[10] Nhóm 5, Báo cáo bài tập lớn môn Kho dữ liệu: Kho dữ liệu sàn thương mại điện tử. Hà Nội: Khoa Viễn thông I, Học viện Công nghệ Bưu chính Viễn thông, 11/2026.',
]

# ---------------------------------------------------------------------------
# Bảng: định nghĩa một lần, dùng cho cả thân bài lẫn danh mục
# ---------------------------------------------------------------------------
TABLES: dict[str, dict] = {
    "abbr": {
        "caption": "Bảng 0.1. Danh mục từ viết tắt",
        "headers": ["Viết tắt", "Tiếng Anh", "Tiếng Việt"],
        "rows": ABBREVIATIONS,
    },
    "phan_cong": {
        "caption": "Bảng 0.2. Phân công nhiệm vụ bốn thành viên Nhóm 9",
        "headers": ["STT", "Họ và tên", "MSSV", "Vai trò chính", "Công việc được giao"],
        "rows": [[str(i + 1), n, m, v, c] for i, (n, m, v, c) in enumerate(THANH_VIEN)],
    },
    "diem": {
        "caption": "Bảng 0.3. Đánh giá đóng góp cá nhân (trọng số 50% – 30% – 20%)",
        "headers": ["Tiêu chí", "Trọng số"] + DIEM_THANH_VIEN,
        "rows": [
            ["Hoàn thành nhiệm vụ", "50%", "48", "48", "48", "48"],
            ["Hợp tác, hỗ trợ nhóm", "30%", "28", "28", "28", "28"],
            ["Trình bày, báo cáo", "20%", "19", "19", "19", "19"],
            ["Tổng điểm cá nhân", "100%", "95", "95", "95", "95"],
        ],
    },
    "dim": {
        "caption": "Bảng 2.1. Danh sách năm chiều trong kho DW_QuanLyHocTap",
        "headers": ["Chiều", "Khóa surrogate", "Thuộc tính tiêu biểu", "Kiểu thay đổi", "Gắn fact"],
        "rows": [
            ["dim_thoi_gian", "date_key", "ngày, thứ, tuần, tháng, quý, năm, học kỳ, năm học", "Type 1", "Cả hai"],
            ["dim_hoc_sinh", "hoc_sinh_key", "ma_hoc_sinh, họ tên, lớp, trạng thái, start_date, end_date, is_current", "Type 2", "Cả hai"],
            ["dim_mon_hoc", "mon_hoc_key", "ma_mon, ten_mon, so_tin_chi, khoa", "Type 1", "Cả hai"],
            ["dim_de_thi", "de_thi_key", "ma_de, ten_de, loai, do_kho, so_cau", "Type 1", "Kết quả thi"],
            ["dim_bai_hoc", "bai_hoc_key", "ma_bai, ten_bai, loai_noi_dung, thoi_luong_phut", "Type 1", "Chuyên cần"],
        ],
    },
    "grain": {
        "caption": "Bảng 2.2. Mức hạt, khóa và số đo của hai bảng fact",
        "headers": ["Fact", "Một dòng là", "Khóa tự nhiên", "Khóa chiều", "Số đo chính", "Cách cuộn lên"],
        "rows": [
            ["fact_ket_qua_thi", "Một lần nộp đã chấm", "lan_lam_id", "hoc_sinh_key, date_key, mon_hoc_key, de_thi_key",
             "diem_so, so_cau_dung, so_cau_sai, tong_so_cau, ty_le_dung, thoi_gian_lam_giay",
             "Đếm lượt, trung bình điểm, tỷ lệ tính lại từ tổng câu"],
            ["fact_chuyen_can", "Một phiên học hoàn thành", "phien_hoc_id", "hoc_sinh_key, date_key, mon_hoc_key, bai_hoc_key",
             "thoi_luong_phut, so_video_da_xem, so_tuong_tac, diem_chuyen_can",
             "Cộng phút và video, trung bình điểm chuyên cần"],
        ],
    },
    "bus": {
        "caption": "Bảng 2.3. Ma trận bus giữa hai fact và năm chiều",
        "headers": ["Chiều", "fact_ket_qua_thi", "fact_chuyen_can", "Vai trò"],
        "rows": [
            ["Thời gian", "Có", "Có", "Dùng chung"],
            ["Học sinh (SCD Type 2)", "Có", "Có", "Dùng chung"],
            ["Môn học", "Có", "Có", "Dùng chung"],
            ["Đề thi", "Có", "Không", "Riêng fact kết quả thi"],
            ["Bài học", "Không", "Có", "Riêng fact chuyên cần"],
        ],
    },
    "rules": {
        "caption": "Bảng 2.4. Bảy luật của cổng chất lượng trước khi nạp fact",
        "headers": ["Luật", "Nguồn", "Điều kiện loại", "Lý do"],
        "rows": [
            ["1", "Bài thi", "tong_so_cau ≤ 0", "Không tính được điểm và tỷ lệ"],
            ["2", "Bài thi", "so_cau_dung hoặc so_cau_sai âm; đúng + sai ≠ tổng", "Số câu không khớp nhau"],
            ["3", "Bài thi", "diem_so ∉ [0, 10] hoặc lệch quá 0,05 so với 10 × đúng / tổng", "Điểm không khớp đáp án"],
            ["4", "Bài thi", "ty_le_dung lệch quá 0,02 so với đúng / tổng", "Tỷ lệ không khớp số câu"],
            ["5", "Bài thi", "thoi_gian_giay ≤ 0 hoặc > 14 400", "Thời gian làm bài bất thường"],
            ["6", "Phiên học", "thoi_luong_giay ≤ 0 hoặc > 28 800; so_video ∉ {0, 1}", "Thời lượng/video không hợp lệ"],
            ["7", "Phiên học", "so_tuong_tac ∉ [0, 200] hoặc diem_chuyen_can ∉ [0, 10]", "Tương tác/điểm ngoài khoảng"],
        ],
    },
    "dict": {
        "caption": "Bảng 2.5. Từ điển dữ liệu (cột tiêu biểu)",
        "headers": ["Bảng", "Cột", "Kiểu", "Ý nghĩa"],
        "rows": [
            ["hoc_sinh (OLTP)", "ma_hs / lop / trang_thai_hoc_vu", "NVARCHAR", "Mã, lớp và trạng thái hiện tại của học sinh"],
            ["lan_lam_bai (OLTP)", "id / ma_hs / ma_de / diem / nop_luc", "INT, NVARCHAR, DECIMAL, DATETIME2", "Một lần nộp bài đã chấm"],
            ["phien_hoc (OLTP)", "id / ma_bai / thoi_luong_giay / diem_chuyen_can", "INT, DECIMAL", "Một phiên học bài"],
            ["su_kien_hoc_vu (OLTP)", "id / thoi_diem / lop_moi / ly_do", "INT, DATETIME2, NVARCHAR", "Nguồn phát sinh phiên bản SCD"],
            ["dim_hoc_sinh", "hoc_sinh_key / start_date / end_date / is_current", "INT, DATETIME2, TINYINT", "Lịch sử học sinh theo SCD Type 2"],
            ["fact_ket_qua_thi", "lan_lam_id / hoc_sinh_key / diem_so", "INT, DECIMAL", "Hạt một lần thi, trỏ đúng phiên bản học sinh"],
            ["fact_chuyen_can", "phien_hoc_id / thoi_luong_phut", "INT, DECIMAL(10,2)", "Hạt một phiên học, phút = giây / 60"],
            ["etl_batch / etl_reject", "src_*, loaded_*, rejected_* / nguon, ly_do", "INT, NVARCHAR", "Đối soát nguồn = nạp + loại và hàng bị loại"],
        ],
    },
    "dagster": {
        "caption": "Bảng 3.1. Năm asset Dagster và hàm ETL tương ứng",
        "headers": ["Thứ tự", "Asset trong Dagster", "Hàm trong app/etl.py", "Việc làm"],
        "rows": [
            ["1", "oltp_extracted_batch", "step_extract", "Đọc theo watermark, ghi ba bảng etl_stage_*"],
            ["2", "quality_gate_checked", "step_quality_gate", "Áp bảy luật, đánh dấu is_valid = 0 và ghi etl_reject"],
            ["3", "dim_hoc_sinh_scd2", "step_scd2", "Đóng bản cũ, chèn bản mới cho chiều học sinh"],
            ["4", "dw_fact_tables", "step_load_facts", "Tra chiều, xử lý unknown member -1, nạp hai fact"],
            ["5", "dw_audit_and_summary", "step_audit", "Đối soát, cập nhật etl_batch, dọn staging"],
        ],
    },
    "ports": {
        "caption": "Bảng 3.2. Hai cổng web của hệ thống",
        "headers": ["Cổng", "Đường dẫn", "Nhiệm vụ", "Nguồn dữ liệu"],
        "rows": [
            ["Tác nghiệp", "/hoc-tap", "Làm đề, nộp bài, bắt đầu phiên học, cập nhật học vụ", "Ghi thẳng OLTP_QuanLyHocTap"],
            ["Phân tích", "/bi", "Dashboard, OLAP, drill-across, chất lượng", "Đọc DW_QuanLyHocTap (bất đồng bộ)"],
        ],
    },
    "seed": {
        "caption": "Bảng 4.1. Số đo sau mẻ nạp trên tập Seed 9",
        "headers": ["Chỉ tiêu", "Giá trị"],
        "rows": [
            ["Học sinh / môn học ở OLTP", "48 / 6"],
            ["Lần nộp ở OLTP và dòng fact_ket_qua_thi", "344 / 344"],
            ["Phiên học ở OLTP và dòng fact_chuyen_can", "822 / 822"],
            ["Sự kiện học vụ / phiên bản chiều học sinh", "51 / 51 (48 đang hiệu lực)"],
            ["Bản ghi bị loại / unknown member", "0 / 0"],
            ["Dòng iv_diem_theo_mon_thang", "109"],
            ["Điểm thi trung bình", "6,72"],
            ["Tổng phút học / điểm chuyên cần TB", "13 197 / 6,71"],
            ["Cặp mã học sinh × môn ở vw_drill_across", "278 (186 cả hai, 15 chỉ điểm, 77 chỉ chuyên cần)"],
            ["Ba cờ đối soát khop_bai, khop_phien, khop_summary", "Đúng cả ba"],
        ],
    },
    "subject": {
        "caption": "Bảng 4.2. Điểm trung bình theo môn trên Seed 9",
        "headers": ["Môn học", "Số lượt", "Điểm TB"],
        "rows": [
            ["Xác suất thống kê", "56", "7,11"],
            ["Tiếng Anh chuyên ngành", "54", "6,85"],
            ["Mạng máy tính", "60", "6,77"],
            ["Lập trình Python", "56", "6,64"],
            ["Cơ sở dữ liệu", "66", "6,55"],
            ["Kho dữ liệu", "52", "6,38"],
            ["Tổng", "344", "6,72"],
        ],
    },
    "scd": {
        "caption": "Bảng 4.3. Lịch sử SCD Type 2 của học sinh B23DCKD004",
        "headers": ["Phiên bản", "hoc_sinh_key", "Lớp", "Start_Date", "End_Date", "Is_Current"],
        "rows": [
            ["1", "1", "D23CQKD03", "05/09/2026 00:00", "12/10/2026 08:00", "0"],
            ["2", "49", "D23CQCN01", "12/10/2026 08:00", "9999-12-31 23:59:59", "1"],
        ],
    },
    "fanout": {
        "caption": "Bảng 4.4. Đối chứng drill-across: B23DCKD004, môn Cơ sở dữ liệu",
        "headers": ["Cách tính", "Số dòng", "Tổng điểm", "Tổng phút"],
        "rows": [
            ["Gộp từng fact rồi FULL OUTER JOIN", "5 bài và 7 phiên (7 dòng)", "26", "110,5"],
            ["JOIN thẳng hai fact", "35 = 5 × 7", "182 = 26 × 7", "552,8 ≈ 110,5 × 5"],
        ],
    },
    "perf": {
        "caption": "Bảng 4.5. So sánh quét fact và đọc indexed view WITH (NOEXPAND)",
        "headers": ["Cách đọc", "Số dòng đọc", "Thời gian 40 vòng", "Ghi chú"],
        "rows": [
            ["fact_ket_qua_thi rồi GROUP BY môn, lớp", "344", "309,6 ms", "Quét hạt nguyên tử"],
            ["iv_diem_theo_mon_thang WITH (NOEXPAND)", "109", "109,2 ms", "Đọc bản đã tổng hợp, tự bảo trì"],
        ],
    },
}

# ---------------------------------------------------------------------------
# Ảnh: chỉ dùng file có thật trong bao-cao/hinh
# ---------------------------------------------------------------------------
FIGURES: dict[str, dict] = {
    "kien_truc": {"file": "kien-truc-tong-va-luong-du-lieu.png", "folder": "so-do", "caption": "Hình 2.1. Kiến trúc tổng thể và luồng dữ liệu của hệ thống"},
    "erd": {"file": "erd-oltp.png", "folder": "so-do", "caption": "Hình 2.2. Sơ đồ thực thể liên kết của CSDL OLTP_QuanLyHocTap"},
    "fact_dim": {"file": "so-do-fact-dim.png", "folder": "so-do", "caption": "Hình 2.3. Sơ đồ Fact – Dimension của kho DW_QuanLyHocTap"},
    "infra": {"file": "ssms_03_danh_sach_database.png", "caption": "Hình 3.1. Hai cơ sở dữ liệu OLTP và DW trong SSMS"},
    "dashboard": {"file": "hinh_3_1_dashboard.png", "caption": "Hình 3.2. Bảng điều khiển trên cổng /bi"},
    "lamde": {"file": "hinh_3_2_lam_de.png", "caption": "Hình 3.3. Cổng /hoc-tap – làm đề và nộp bài"},
    "dsv": {"file": "vs_06_dsv_full.png", "caption": "Hình 3.4. Data Source View của khối HocTapOLAP trong SSDT"},
    "dim": {"file": "vs_07_dim.png", "caption": "Hình 3.5. Chiều và hierarchy trong dự án SSDT"},
    "scd": {"file": "hinh_3_3_scd.png", "caption": "Hình 4.1. Tra cứu lịch sử SCD Type 2 của B23DCKD004"},
    "drill_ui": {"file": "hinh_4_1_drill_across.png", "caption": "Hình 4.2. Kết quả drill-across trên cổng /bi"},
    "drill_ssms": {"file": "ssms_04_ket_qua_drill_across.png", "caption": "Hình 4.3. Kết quả vw_drill_across trên SSMS"},
    "ssms_io": {"file": "hinh_4_2_ssms_query.png", "caption": "Hình 4.4. Truy vấn đối soát trên SSMS"},
    "excel_roll": {"file": "excel_01_rollup.png", "caption": "Hình 4.5. Roll-up trên Excel PivotTable"},
    "excel_pivot": {"file": "excel_05_pivot.png", "caption": "Hình 4.6. Pivot lớp và môn trên Excel PivotTable"},
}

MISSING_IMAGES = [
    "Ảnh chụp riêng Execution Plan và STATISTICS IO trên SSMS",
]

# ---------------------------------------------------------------------------
# Nội dung thân bài – một nguồn dữ liệu cho cả danh mục lẫn văn bản
# block: ("h1"|"h2", text, newpage?) | ("p", text) | ("table", key)
#        | ("fig", key, width_cm) | ("ref",) | ("pagebreak",)
# ---------------------------------------------------------------------------
BLOCKS: list[tuple] = [
    ("h1", "PHẦN MỞ ĐẦU", True),
    ("h2", "1. Tính cấp thiết của đề tài"),
    ("p", "Học phần Kho dữ liệu (DAE 1408) yêu cầu nhóm không dừng lại ở bài tập truy vấn rời mà phải dựng được một sản phẩm chạy được. Đề tài nhóm chọn là hệ thống quản lý học tập và ôn luyện trực tuyến: học sinh xem bài, làm đề, nộp bài; cán bộ học vụ đổi lớp, cho bảo lưu hoặc gắn cảnh báo. Những việc này phát sinh liên tục, không phải một file Excel nộp một lần."),
    ("p", "Nếu phân tích trực tiếp trên bảng tác nghiệp, câu hỏi phân tích dễ bị lẫn với giao dịch đang mở. Theo yêu cầu của giảng viên hướng dẫn, nhóm 9 cần có nguồn OLTP mô phỏng, hai fact độc lập, chiều học sinh kiểu SCD Type 2, tầng tổng hợp bằng indexed view và khối đa chiều SSAS. Bản báo cáo này mô tả đúng những gì đang chạy trong thư mục BTL_KhoDL, không mô tả một thiết kế chỉ có trên giấy."),

    ("h2", "2. Mục tiêu và phạm vi nghiên cứu"),
    ("p", "Mục tiêu của bài là dựng được kho hình chòm sao cho bài toán học và thi, rồi thao tác được trên giao diện khi bảo vệ trực tiếp. Nhóm không làm slide; người nghe nhìn sản phẩm đang chạy và tự đặt câu hỏi trên dữ liệu thật."),
    ("p", "Các đầu việc cụ thể gồm: nguồn OLTP có học sinh, môn, đề, câu hỏi, bài học, lần làm bài, phiên học và sự kiện học vụ; fact kết quả thi và fact chuyên cần dùng chung thời gian, học sinh, môn; SCD Type 2 với start_date, end_date, is_current; cổng chất lượng và đối soát số dòng; tầng tổng hợp; năm thao tác OLAP cộng thêm drill-across; bộ sinh dữ liệu mẫu; hai cổng web; khối SSAS và Excel PivotTable."),

    ("h2", "3. Đối tượng và dữ liệu thử nghiệm"),
    ("p", "Đối tượng dữ liệu là học sinh đại học đang học, luyện đề và xem bài trên một hệ mô phỏng. Nhóm sinh 48 học sinh ở bốn lớp D23CQCN01, D23CQKT02, D23CQKD03 và D23CQVT04. Bốn thành viên nhóm có mặt trong danh mục học sinh với mã B23DCKD004, B23DCKD008, B23DCKD014 và B23DCKD030, để thao tác trực tiếp trên dữ liệu mẫu. Báo cáo là sản phẩm bảo vệ chung của Nhóm 9."),
    ("p", "Sáu môn gồm Cơ sở dữ liệu, Kho dữ liệu, Lập trình Python, Mạng máy tính, Xác suất thống kê và Tiếng Anh chuyên ngành. Mỗi môn có một đề luyện, một đề kiểm tra năm câu và ba bài học. Dữ liệu lịch sử nằm trong các ngày làm việc từ 08/09/2026 đến 03/11/2026, học kỳ HK1 năm học 2026-2027. Nguồn không nối vào cổng đào tạo thật của học viện. Máy dùng để đo là laptop Windows, Python 3.12, SQL Server cài local và ODBC Driver 17."),

    ("h2", "4. Phương pháp tiếp cận và công cụ thực thi"),
    ("p", "Nhóm đi theo lộ trình giảng viên hướng dẫn: tách OLTP khỏi kho theo hướng Inmon, rồi thiết kế chiều theo bốn bước của Kimball [1], [2]. Web app dùng Python 3.12 với FastAPI [7] và pyodbc. Hệ quản trị duy nhất là Microsoft SQL Server: OLTP_QuanLyHocTap giữ tám bảng tác nghiệp đã chuẩn hóa, DW_QuanLyHocTap là kho. Kết nối mặc định là localhost, Trusted_Connection=yes (Windows Authentication) kèm TrustServerCertificate=yes [5]. Mọi dữ liệu nghiệp vụ và dữ liệu phân tích đều nằm trên hệ quản trị này."),
    ("p", "Bộ sinh mockup_generator/generate_sample_data.py nạp kỳ mẫu với bộ sinh số cố định seed 9. ETL chạy native trên Windows bằng Dagster [6] tại http://127.0.0.1:3000 theo lịch */2 * * * *, gọi lần lượt năm hàm step_* trong app/etl.py. Web app chỉ ghi OLTP và đọc DW; Dagster là nơi duy nhất điều phối các mẻ ETL. Kiểm tra logic nằm ở lệnh python -m app.selfcheck, hiện đạt 31 ca."),

    ("h2", "5. Bố cục của báo cáo"),
    ("p", "Chương 1 chốt bài toán và các khái niệm dùng xuyên suốt: hạt fact, chiều dùng chung, SCD Type 2, cổng chất lượng, OLAP và drill-across. Chương 2 là thiết kế: kiến trúc, ma trận bus, hai fact, bảy luật loại bản ghi, unknown member và từ điển dữ liệu. Chương 3 là cách cài đặt SQL Server, bộ sinh Seed 9, Dagster, hai cổng web, indexed view và khối SSDT. Chương 4 ghi số đo trên tập Seed 9 gồm đối soát dòng, SCD Type 2, drill-across chống fan-out và indexed view. Kết luận nêu phần đã chạy và hướng làm mới khối SSAS sau mỗi mẻ."),

    ("h1", "CHƯƠNG 1. TỔNG QUAN BÀI TOÁN VÀ CƠ SỞ LÝ THUYẾT", True),
    ("h2", "1.1. Bài toán và bối cảnh thực tiễn"),
    ("p", "Một buổi học trên hệ thống này có hai việc khác nhau. Việc thứ nhất là nộp bài: hệ thống chấm số câu đúng, quy điểm trên thang 10 và lưu thời gian làm. Việc thứ hai là học bài: học sinh mở video hoặc tài liệu, hệ thống cộng phút, đếm số tương tác và tính một điểm chuyên cần nội bộ. Hai việc không cùng mức chi tiết. Một học sinh có thể nộp hai bài Cơ sở dữ liệu nhưng xem bảy phiên bài giảng, hoặc chỉ học mà chưa thi."),
    ("p", "Cán bộ học vụ còn sửa hồ sơ: chuyển lớp, bảo lưu, cảnh báo học vụ, rồi cho học tiếp. Nếu bảng học sinh chỉ giữ trạng thái mới nhất, bài thi tháng 9 sẽ bị gắn nhầm vào lớp tháng 10. Câu hỏi cần trả lời khi chấm là liệu fact cũ có bị viết lại hay không. Vì vậy chiều học sinh phải giữ lịch sử, còn fact chỉ trỏ tới phiên bản đúng tại thời điểm phát sinh sự kiện."),
    ("p", "Nhóm giữ unknown member khóa -1, đặt cổng kiểm tra trước khi nạp fact và đối soát số dòng ở cuối mẻ. Khối SSAS lấy nguồn từ DW_QuanLyHocTap, không đọc bảng OLTP. Kịch bản bảo vệ vẫn là thêm một dòng ở nguồn, chạy mẻ Dagster, kho và màn hình đổi số, sau đó process lại khối để Excel thấy dòng mới."),

    ("h2", "1.2. Cơ sở lý thuyết nền tảng"),
    ("p", "Inmon mô tả kho là dữ liệu tích hợp, gắn thời gian, ổn định và hướng chủ đề; ông cũng tách hạt nguyên tử khỏi tầng tổng hợp [1]. Nhóm hiểu ổn định theo nghĩa không sửa điểm một bài đã nạp chỉ vì hôm sau học sinh đổi lớp. Bài đó vẫn là sự kiện của ngày nó xảy ra."),
    ("p", "Kimball thiết kế kho từ quy trình nghiệp vụ và mức hạt, rồi mới chọn chiều và số đo [2]. Các fact khác nhau được phép dùng chung một số chiều; đó là kiến trúc bus. Khi có từ hai fact trở lên mà vẫn dùng chung chiều, lược đồ gọi là fact constellation. Nhóm có đúng hai fact, dùng chung thời gian, học sinh và môn; đề thi chỉ gắn fact kết quả, bài học chỉ gắn fact chuyên cần."),
    ("p", "Cùng tài liệu đó mô tả SCD Type 2: khi thuộc tính cần lưu lịch sử thay đổi, đóng bản ghi cũ bằng ngày kết thúc rồi thêm bản mới với khóa surrogate khác [2]. Nhóm áp dụng cho lớp và trạng thái học vụ, còn họ tên coi như không đổi trong phạm vi bài. Kimball cũng khuyên không nối hai fact trực tiếp khi hạt lệch nhau, vì một bài thi sẽ lặp theo số phiên học và tổng điểm bị nhân lên."),
    ("p", "Thuật ngữ OLAP gắn với bài của Codd, Codd và Salley năm 1993: phân tích xoay quanh nhiều chiều chứ không chỉ một câu hỏi tác nghiệp [3]. Năm thao tác nhóm làm là Roll-up (cuộn lên mức thô hơn), Drill-down (khoan xuống mức mịn hơn), Slice (cố định một chiều), Dice (cắt nhiều điều kiện cùng lúc) và Pivot (đổi hàng với cột). Drill-across là thao tác thêm: gộp từng fact về cùng hạt rồi mới nối."),
    ("p", "Trước fact cần một cổng chất lượng. Kimball và Caserta mô tả việc đo số bản ghi đọc được, nạp được và bị loại để người vận hành biết dòng có rơi giữa đường hay không [4]. Unknown member là lối thoát khi mã học sinh hoặc mã đề không tra được chiều: fact vẫn vào kho với khóa -1 thay vì bị xóa im lặng. Nhóm tách hai việc này: sai logic số đo thì loại, sai mã danh mục thì giữ nhưng đánh dấu không xác định."),

    ("h2", "1.3. Công nghệ sử dụng"),
    ("p", "Tầng lưu trữ gồm hai CSDL SQL Server tách biệt, tạo và khởi tạo tự động từ sql/app_oltp.sql và sql/app_dw.sql. Ứng dụng nối qua pyodbc với ODBC Driver 17; chuỗi kết nối dùng Windows Authentication theo mặc định và cho phép ghi đè bằng biến môi trường nếu cần [5]. Collation là Vietnamese_CI_AS để tiếng Việt không bị lỗi encoding."),
    ("p", "Tầng điều phối là Dagster chạy native trên Windows, giao diện ở cổng 3000, thể hiện cây Assets Lineage và nút Materialize all [6]. Tầng web là FastAPI với hai trang tĩnh [7]. Tầng phân tích gồm indexed view trên SQL Server [8] và khối đa chiều dựng trong Visual Studio SSDT, đọc bằng Excel PivotTable [9]."),

    ("h1", "CHƯƠNG 2. PHÂN TÍCH VÀ THIẾT KẾ KHO DỮ LIỆU", True),
    ("h2", "2.1. Yêu cầu chức năng và kiến trúc hệ thống"),
    ("p", "Yêu cầu chức năng bám sát góp ý của giảng viên hướng dẫn. Nguồn phải nhận bài nộp và phiên học từ form, không chỉ phát file CSV. Quản trị phải đổi được lớp và trạng thái để SCD sinh bản mới ngay trước mắt. Bộ sinh phải bắn nhiều học sinh trong một nhịp, có cả bản ghi bẩn. Dashboard đọc số từ kho, không đọc thẳng bảng OLTP để vẽ điểm trung bình. Trang OLAP trên web và PivotTable trên khối SSAS phải làm được Roll-up, Drill-down, Slice, Dice và Pivot."),
    ("p", "Kiến trúc vận hành gồm cổng web, OLTP_QuanLyHocTap, Dagster, DW_QuanLyHocTap và ba lối đọc. Cổng /hoc-tap ghi bài nộp và phiên học thẳng vào OLTP. Năm asset Dagster kiểm tra số đo, tra chiều, áp dụng SCD Type 2 rồi nạp fact. Cổng /bi đọc indexed view và các view đối soát; Excel đọc khối SSAS. Hình 2.1 tóm tắt luồng đi của dữ liệu; hai CSDL được tạo sẵn trong SSMS như Hình 3.1. Cách trình bày sơ đồ kiến trúc và luồng dữ liệu ở đây có tham khảo báo cáo của Nhóm 5 [10]."),
    ("fig", "kien_truc", 12.5),
    ("fig", "infra", 12.5),
    ("p", "Nhóm không dựng thêm cơ sở staging vật lý riêng ngoài ba bảng etl_stage_exam, etl_stage_session và etl_stage_event nằm trong DW. Watermark trên ba luồng lan_lam_bai, phien_hoc và su_kien_hoc_vu đóng vai trò mốc trích xuất. Bản ghi đã qua mẻ, kể cả bản bị loại, không bị đọc lại. Đây là một hạn chế: nếu sửa đúng dòng bẩn tại chỗ mà giữ nguyên id, kho sẽ không hút lại; muốn nạp lại thì phải phát sinh id mới."),

    ("h2", "2.2. Nguồn OLTP 3NF"),
    ("p", "Nguồn tác nghiệp OLTP_QuanLyHocTap có tám bảng và dừng ở dạng chuẩn 3NF: hoc_sinh, mon_hoc, de_thi, cau_hoi, bai_hoc, lan_lam_bai, phien_hoc và su_kien_hoc_vu. Mỗi thuộc tính phụ thuộc vào khóa của đúng bảng đó, không phụ thuộc bắc cầu. Mã học sinh cố ý không làm khóa ngoại của lần nộp: nguồn được phép phát sinh mã lạ, còn kho mới quyết định đưa fact về unknown member."),
    ("p", "Ba bảng sự kiện lan_lam_bai, phien_hoc và su_kien_hoc_vu dùng khóa IDENTITY làm khóa tự nhiên. Cột trang_thai của bài nộp và phiên học được dùng để lọc chỉ bản ghi đã hoàn tất. Các chỉ số nonclustered trên ma_hs phục vụ việc đọc theo watermark từng luồng. Hình 2.2 là sơ đồ thực thể liên kết của tám bảng nguồn."),
    ("fig", "erd", 12.5),

    ("h2", "2.3. Thiết kế chòm sao và các chiều"),
    ("p", "Kho DW_QuanLyHocTap là fact constellation gồm hai fact và năm chiều. Mọi chiều đều có bản ghi unknown với khóa -1 để khóa ngoại của fact không bị gãy. Hình 2.3 mô tả quan hệ Fact – Dimension; cách thể hiện sơ đồ này tham khảo từ báo cáo của Nhóm 5 [10]. Bảng 2.1 liệt kê năm chiều, Bảng 2.2 nêu mức hạt cùng số đo, Bảng 2.3 là ma trận bus giữa hai fact và năm chiều."),
    ("fig", "fact_dim", 12.5),
    ("table", "dim"),
    ("table", "grain"),
    ("table", "bus"),
    ("p", "Mức hạt của fact kết quả là một lần nộp đã chấm; số đo gồm điểm, số câu đúng, số câu sai, tổng số câu, tỷ lệ đúng và thời gian tính bằng giây. Điểm và tỷ lệ là số đo không cộng được khi cuộn lên: báo cáo cuộn dùng trung bình điểm và tính lại tỷ lệ từ tổng câu đúng chia tổng câu. Mức hạt của fact chuyên cần là một phiên học hoàn thành, số đo là phút học, số video (0 hoặc 1), số tương tác và điểm chuyên cần. Hai hạt này cố ý không bằng nhau."),
    ("p", "Chiều thời gian sinh sẵn từ 01/08/2026 đến 30/06/2027, khóa là số YYYYMMDD. Tháng 9 đến tháng 12 và tháng 1 thuộc HK1; tháng 2 đến tháng 6 thuộc HK2; tháng 7 là học hè. Chiều môn, đề và bài học là SCD Type 1: đổi tên thì cập nhật tại chỗ. Khóa ngoại của hai fact đều có nonclustered index; cột loai_bai chỉ có THI và LUYEN_DE, cột loai_noi_dung chỉ có VIDEO và TAI_LIEU."),

    ("h2", "2.4. SCD Type 2 và unknown member"),
    ("p", "Một dòng trong dim_hoc_sinh có hoc_sinh_key, mã, họ tên, lớp, trạng thái, lý do, start_date, end_date, is_current và version_no. Bản hiện tại có end_date bằng 9999-12-31 23:59:59. Khi có sự kiện học vụ mới, ETL đóng bản cũ tại đúng thời điểm sự kiện rồi chèn bản mới với khóa surrogate lớn hơn. View vw_dim_hoc_sinh_scd đổi tên cột sang Start_Date, End_Date và Is_Current để thuận tiện khi đối chiếu trên SSMS."),
    ("p", "Trong một mẻ, sự kiện học vụ được áp dụng hết trước, fact nạp sau. Nhờ vậy bài nộp cùng nhịp với lần chuyển lớp vẫn tra được phiên bản mới. Fact không lấy bản is_current; fact dò bản có start_date nhỏ hơn hoặc bằng thời điểm nộp và end_date lớn hơn thời điểm đó. Kết quả là bài cũ giữ nguyên khóa cũ dù hồ sơ hiện tại đã đổi."),
    ("p", "Unknown member dùng khi mã học sinh hoặc mã đề không tra được chiều. Bài có mã lạ nhưng số đo hợp lệ vẫn vào fact với hoc_sinh_key = -1 và được đếm riêng ở cột unknown_exam của etl_batch. Cách này giữ được đẳng thức nguồn = nạp + loại mà không làm rơi dòng."),

    ("h2", "2.5. Cổng chất lượng bảy luật"),
    ("p", "Cổng chất lượng nằm ở bước step_quality_gate, trước khi nạp fact. Hàng vi phạm bị đánh dấu is_valid = 0 trong bảng staging, ghi lý do vào etl_reject và không được chèn vào fact. Bảng 2.4 gom các kiểm tra trong validate_exam và validate_session thành bảy luật dễ nhớ."),
    ("table", "rules"),
    ("p", "Luật 3 và luật 4 so sánh điểm và tỷ lệ với số câu đúng thay vì chỉ kiểm tra khoảng giá trị, nên một bài có điểm 10 nhưng chỉ đúng 3/5 câu vẫn bị loại. Ngược lại, mã học sinh không có trong chiều không bị loại: đó là unknown member, không phải lỗi số đo."),

    ("h2", "2.6. Tầng tổng hợp và view đối soát"),
    ("p", "Tầng tổng hợp trên SQL Server gồm hai indexed view. iv_diem_theo_mon_thang gom fact thi theo năm, tháng, môn, lớp tại thời điểm thi và loại bài. iv_chuyen_can_theo_lop_tuan gom theo tuần. Cả hai dùng WITH SCHEMABINDING, COUNT_BIG và một unique clustered index [8]. Trung bình điểm không nằm trong indexed view mà được tính ở view vw_diem_theo_mon_thang bằng SUM chia số lượt."),
    ("p", "Drill-across nằm ở vw_drill_across dạng WITH rồi FULL OUTER JOIN giữa hai câu đã GROUP BY về hạt mã học sinh × môn. View này không được đánh chỉ mục cụm vì SQL Server không cho outer join trong indexed view. Dashboard đọc iv_diem_theo_mon_thang WITH (NOEXPAND) để chắc chắn dùng đúng bản đã tổng hợp."),
    ("p", "Bảng etl_batch lưu số dòng nguồn, nạp, loại, unknown và số phiên bản SCD mới của từng mẻ. Bất biến được giữ ở bước audit là: với mỗi luồng, Nguồn = Nạp + Loại. Ba cờ khop_bai, khop_phien và khop_summary trong app/olap.py kiểm tra lại đẳng thức này cùng sự khớp giữa fact và summary."),

    ("h2", "2.7. Từ điển dữ liệu"),
    ("p", "Bảng 2.5 ghi nghĩa của các cột tiêu biểu ở hai CSDL. Đây là tài liệu đối chiếu khi thao tác trực tiếp trên SSMS, tránh nhầm giữa id của OLTP và khóa surrogate của kho."),
    ("table", "dict"),

    ("h1", "CHƯƠNG 3. HIỆN THỰC HÓA HỆ THỐNG", True),
    ("h2", "3.1. Cấu trúc mã nguồn và hạ tầng SQL Server"),
    ("p", "Mã nguồn chia theo việc. sql/app_oltp.sql và sql/app_dw.sql là lược đồ ứng dụng được app/database.py áp dụng khi khởi động nếu đối tượng chưa có. sql/06_sqlserver_dw_and_indexed_views.sql là bản dựng lại trong SSMS. mockup_generator/generate_sample_data.py sinh kỳ mẫu. app/etl.py chứa cổng chất lượng và năm bước ETL. app/olap.py đọc indexed view và fact. app/main.py là API web. orchestration/etl_assets.py là định nghĩa Dagster."),
    ("p", "Hai CSDL được tạo với đường dẫn tệp trong thư mục data/, collation Vietnamese_CI_AS. Mọi kết nối đi qua pyodbc, chuỗi mặc định SERVER=localhost; Trusted_Connection=yes; TrustServerCertificate=yes; Encrypt=no [5]. Lớp SqlConn trong app/database.py dịch LIMIT sang TOP và INSERT OR IGNORE sang INSERT có kiểm tra trùng để cùng một mã nguồn chạy được trên SQL Server."),

    ("h2", "3.2. Bộ sinh dữ liệu mẫu Seed 9"),
    ("p", "mockup_generator/generate_sample_data.py dùng random.Random(9) nên mỗi lần sinh lại ra cùng một tập dữ liệu. Kết quả là 48 học sinh, sáu môn, 344 lần nộp, 822 phiên học và 51 sự kiện học vụ. Bốn mã B23DCKD004, B23DCKD008, B23DCKD014 và B23DCKD030 mặc định được giữ khỏi bộ sinh ngẫu nhiên để hồ sơ lúc trình bày không bị dòng ngẫu nhiên đè lên."),
    ("p", "Bộ sinh cố ý tạo thêm các ca đặc biệt: một học sinh chỉ có phiên học, một học sinh chỉ có bài thi, một học sinh bảo lưu, một học sinh bị cảnh báo và một học sinh đổi lớp. Nhờ đó drill-across có dòng trống ở một bên, còn SCD Type 2 có sự kiện thay đổi thật để kiểm chứng."),

    ("h2", "3.3. Điều phối ETL bằng Dagster"),
    ("p", "orchestration/etl_assets.py định nghĩa năm @asset nối tiếp nhau theo dependency, chạy bởi job dw_quan_ly_hoc_tap_etl với lịch */2 * * * *. Mỗi asset gọi một hàm step_* trong app/etl.py và truyền kết quả xuống asset sau. Khi không có dữ liệu mới theo watermark, các asset sau bỏ qua và ghi nhận BO_QUA. Bảng 3.1 tóm tắt năm bước."),
    ("table", "dagster"),
    ("p", "Ba bảng etl_stage_exam, etl_stage_session và etl_stage_event nhận dữ liệu thô ở bước extract; cổng chất lượng chỉnh cờ is_valid; bước cuối xóa staging sau khi đã cập nhật etl_batch. Cách này giúp mỗi mẻ có thể đối soát độc lập và không để hàng bị loại lẫn vào fact."),
    ("p", "Bước audit in ra đường đối soát dạng exam: 344=344+0 và session: 822=822+0. Nếu một trong hai vế lệch, selfcheck sẽ dừng ở ca tương ứng thay vì báo chung chung là ETL chạy xong."),

    ("h2", "3.4. Hai cổng web"),
    ("p", "Cổng /hoc-tap là nơi tác nghiệp. FastAPI nhận bài nộp, chấm theo đáp án trong OLTP rồi mới ghi lần làm; trình duyệt không nhận đáp án trước khi nộp [7]. Phiên học do server tính điểm: 70 phần trăm theo tỷ lệ thời lượng so với bài chuẩn, 30 phần trăm theo số tương tác nhưng không quá mười lần bấm, trần là 10 điểm."),
    ("p", "Cổng /bi là nơi phân tích. Dashboard lấy điểm trung bình theo môn từ iv_diem_theo_mon_thang, các nút OLAP gọi app/olap.py để sinh SQL và bảng kết quả, trang chất lượng đọc etl_batch và etl_reject. Việc đọc kho diễn ra bất đồng bộ với việc ghi OLTP: web không khởi động ETL, Dagster mới là nơi điều phối."),
    ("fig", "dashboard", 12.5),
    ("fig", "lamde", 12.5),
    ("table", "ports"),

    ("h2", "3.5. Tối ưu bằng indexed view"),
    ("p", "Hai indexed view được khai báo WITH SCHEMABINDING kèm unique clustered index, nên SQL Server tự bảo trì khi fact thay đổi [8]. Dashboard không phải xóa rồi chèn lại một bảng tổng hợp thủ công. Khi truy vấn, dùng WITH (NOEXPAND) để optimizer đọc trực tiếp chỉ mục của view thay vì mở rộng định nghĩa."),
    ("p", "Với tập Seed 9, iv_diem_theo_mon_thang chỉ còn 109 dòng thay vì 344 dòng của fact. Con số này là lý do chính để dùng tầng tổng hợp; phần đo thời gian được ghi lại ở Chương 4 kèm lưu ý về cỡ dữ liệu còn nhỏ."),

    ("h2", "3.6. Khối đa chiều SSAS và Excel PivotTable"),
    ("p", "Dự án HocTapOLAP nằm trong Visual Studio SSDT. Data Source trỏ tới DW_QuanLyHocTap; DSV chọn đúng bảy bảng gồm hai fact và năm chiều, không kéo quan hệ giữa hai bảng fact [9]. Chiều học sinh dùng hoc_sinh_key làm khóa vì cùng một ma_hoc_sinh có nhiều dòng SCD."),
    ("p", "Cube có hai measure group là Ket qua thi va Chuyen can. Ba chiều thời gian, học sinh, môn gắn cả hai nhóm đo; đề chỉ gắn kết quả thi, bài học chỉ gắn chuyên cần. Partition MOLAP có thể bật Proactive Caching với khoảng im lặng khoảng mười giây để Excel Refresh thấy dòng mới."),
    ("p", "Excel PivotTable kết nối vào cube HocTapOLAP và thực hiện năm thao tác ở mục 4.5. Lưu ý quan trọng: sau khi DW có dữ liệu mới từ Dagster, khối SSAS cần được Process lại thì Excel mới thấy số liệu mới; web /bi thì đọc thẳng SQL Server nên không cần bước này."),

    ("h1", "CHƯƠNG 4. THỰC NGHIỆM, KIỂM CHỨNG VÀ ĐÁNH GIÁ", True),
    ("h2", "4.1. Tập đo và môi trường thực nghiệm"),
    ("p", "Mọi số liệu trong chương này đo trên tập Seed 9 vừa sinh, chạy trên laptop Windows, Python 3.12, SQL Server cài local và pyodbc. Khi chạy python -m app.selfcheck, chương trình tạo CSDL có hậu tố _KiemTra, nạp Seed 9, chạy hai mẻ ETL rồi xóa CSDL đó, nên không làm đổi dữ liệu demo. Kết quả là 31 ca đều đạt."),
    ("table", "seed"),
    ("table", "subject"),
    ("p", "Tổng lượt sáu môn là 56 + 54 + 60 + 56 + 66 + 52 = 344, khớp số dòng fact. Đây là dữ liệu giả lập có kiểm soát, không phải phổ điểm thật của lớp. Các con số 6,72 điểm thi trung bình và 13 197 phút học chỉ có nghĩa trong phạm vi Seed 9."),

    ("h2", "4.2. Kiểm chứng SCD Type 2"),
    ("p", "Học sinh B23DCKD004 có đúng hai phiên bản. Bản 1 khóa 1, lớp D23CQKD03, từ 05/09/2026 đến 12/10/2026 08:00, is_current = 0. Bản 2 khóa 49, lớp D23CQCN01, từ 12/10/2026 08:00 đến 9999-12-31, is_current = 1. End_Date của bản cũ trùng Start_Date của bản mới, đúng yêu cầu SCD Type 2."),
    ("table", "scd"),
    ("fig", "scd", 12.5),
    ("p", "Câu kiểm chứng nằm trong selfcheck: không có bài trước 12/10 gắn bản 2 và không có bài từ 12/10 gắn bản 1. Bài ngày 28/09 môn Xác suất thống kê trỏ khóa 1 và lớp KD03; bài ngày 20/10 môn Cơ sở dữ liệu trỏ khóa 49 và lớp CN01. Khi phát sinh thêm sự kiện cảnh báo học vụ, bản 3 mở ra nhưng các bài tháng 9 và tháng 10 vẫn giữ khóa cũ."),

    ("h2", "4.3. Drill-across chống fan-out"),
    ("p", "Trên toàn tập, vw_drill_across trả 278 cặp mã học sinh × môn: 186 cặp có cả điểm lẫn phút, 15 cặp chỉ có điểm, 77 cặp chỉ có chuyên cần. FULL OUTER JOIN giữ lại 92 cặp mà inner join sẽ làm mất. Đây là mặt đúng của drill-across."),
    ("p", "Mặt còn lại là chống nhân bản. Chọn B23DCKD004 và môn Cơ sở dữ liệu vì tích 5 nhân 7 đủ nhỏ để nhẩm. Học sinh này có 5 lượt thi, tổng 26 điểm và 7 phiên học, tổng 110,5 phút. Nối thẳng hai fact theo cùng học sinh và môn cho ra 35 dòng, tổng điểm thành 182 và tổng phút thành 552,8. Các con số 35 = 5 × 7 và 182 = 26 × 7 đúng là hệ quả của việc nhân hạt."),
    ("table", "fanout"),
    ("fig", "drill_ui", 12.5),
    ("fig", "drill_ssms", 12.5),
    ("p", "Cách sửa là gộp từng fact về hạt mã học sinh × môn trước, rồi FULL OUTER JOIN theo hai chiều dùng chung. Câu truy vấn nằm ở vw_drill_across trong app_dw.sql và app/olap.py. Bảng kết quả cuối cùng giữ đúng 5 bài, 26 điểm, 7 phiên và 110,5 phút, không bị nhân."),

    ("h2", "4.4. Indexed view, Execution Plan và STATISTICS IO"),
    ("p", "So sánh trực tiếp hai cách đọc: quét fact_ket_qua_thi rồi GROUP BY môn và lớp phải đọc 344 dòng, trong khi iv_diem_theo_mon_thang WITH (NOEXPAND) chỉ đọc 109 dòng. Trên SSMS, bật SET STATISTICS IO ON và SET STATISTICS TIME ON rồi chạy hai câu liên tiếp để thấy logical reads và thời gian của từng bên [8]."),
    ("table", "perf"),
    ("fig", "ssms_io", 12.5),
    ("p", "Đo 40 vòng liên tiếp trên cùng máy cho kết quả 309,6 ms khi quét fact và 109,2 ms khi đọc indexed view. Con số này là thời gian đi qua pyodbc, không phải phép đo thuần trong SSMS. Với 344 dòng thì chênh lệch chưa lớn; nhóm không nói indexed view nhanh hơn hàng chục lần. Lợi ích nhìn thấy ngay là số dòng phải đọc giảm từ 344 xuống 109 và view tự cập nhật khi fact đổi."),
    ("p", "Execution Plan trên SSMS cho thấy câu dùng WITH (NOEXPAND) đọc trực tiếp unique clustered index ux_iv_diem_theo_mon_thang, còn câu quét fact phải dùng nonclustered index rồi làm GROUP BY. Ảnh chụp riêng cho Execution Plan và STATISTICS IO hiện chưa có trong thư mục ảnh; nhóm liệt kê ở phần tổng kết để bổ sung trước khi bảo vệ."),

    ("h2", "4.5. Năm thao tác OLAP trên Excel PivotTable"),
    ("p", "Roll-up để hierarchy H_ThoiGian ở mức Năm học và Học kỳ gom các tháng thành một dòng HK1 2026-2027, vẫn 344 lượt và điểm trung bình 6,72. Drill-down mở dấu cộng tại học kỳ để xem ba tháng 9, 10, 11. Slice cố định môn Kho dữ liệu. Dice cắt thêm lớp D23CQKD03 và khoảng 01/09 đến 04/11. Pivot đưa lớp xuống hàng, môn sang cột rồi đổi chỗ để xoay cùng một khối."),
    ("fig", "excel_roll", 12.5),
    ("fig", "excel_pivot", 12.5),
    ("p", "Trên cổng /bi, năm nút tương ứng trả về câu SQL vừa thực thi và bảng kết quả, nên có thể đối chiếu ngay với PivotTable. Không kéo đồng thời số lượt của hai measure group rồi nhân chúng; muốn so điểm và phút thì dùng vw_drill_across làm bản đối soát đúng hạt."),

    ("h2", "4.6. Đánh giá kết quả và hạn chế"),
    ("p", "Kết quả đạt được là hai CSDL SQL Server tách biệt, tám bảng OLTP 3NF, hai fact, năm chiều, unknown member -1, SCD Type 2, cổng chất lượng bảy luật, đối soát Nguồn = Nạp + Loại, hai cổng web, tầng tổng hợp và khối SSAS. Bộ sinh Seed 9 cho cùng một tập số liệu mỗi lần chạy, còn selfcheck phủ 31 ca cần đối chiếu khi bảo vệ."),
    ("p", "Hạn chế thứ nhất là dữ liệu mô phỏng, câu hỏi trắc nghiệm ngắn và thời gian chỉ trải từ tháng 9 đến tháng 11. Hạn chế thứ hai là watermark không xử lý lại dòng đã loại nếu người dùng sửa cùng id. Hạn chế thứ ba là chưa có đăng nhập, người bảo vệ chọn học sinh trên danh sách. Với 344 dòng, chênh lệch thời gian giữa indexed view và quét fact chưa thể hiện lợi thế ở quy mô triệu dòng."),
    ("p", "Hướng phát triển gần nhất là bật proactive caching cho partition MOLAP với khoảng im lặng mười giây để Excel Refresh thấy bài nộp mới sau khi Dagster đã đẩy sang SQL Server. Hàng bị loại nên tách thành hàng đợi sửa và được nạp lại sau khi OLTP chỉnh xong. Lược đồ hai fact và chiều dùng chung đã cố định nên không phải thiết kế lại khối."),

    ("h1", "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", True),
    ("p", "Nhóm đã hoàn thành hệ thống quản lý học tập và ôn luyện trực tuyến chạy hoàn toàn trên Microsoft SQL Server. Nguồn OLTP nhận nghiệp vụ thật từ cổng /hoc-tap, Dagster điều phối năm bước ETL sang DW_QuanLyHocTap, cổng /bi đọc tầng tổng hợp và khối HocTapOLAP phục vụ Excel PivotTable. Trên tập Seed 9, mọi đối soát đều khớp: 344 bài, 822 phiên, 51 phiên bản học sinh và 109 dòng indexed view."),
    ("p", "Ba điểm nhấn kỹ thuật đã được kiểm chứng bằng số liệu: SCD Type 2 giữ đúng lớp tại thời điểm nộp cho B23DCKD004; vw_drill_across tránh nhân 5 bài với 7 phiên thành 35 dòng; iv_diem_theo_mon_thang giảm số dòng phải đọc từ 344 xuống 109. Selfcheck đạt 31/31."),
    ("p", "Phần còn thiếu chủ yếu là ảnh chụp Execution Plan và STATISTICS IO, cùng bản xuất PNG của hai sơ đồ .drawio. Đây không làm sai số liệu nhưng cần bổ sung để hồ sơ bảo vệ đầy đủ. Khi DW có dữ liệu mới, nhớ process lại khối SSAS trước khi đọc trên Excel."),

    ("h1", "TÀI LIỆU THAM KHẢO", True),
    ("ref",),

    ("h1", "PHỤ LỤC", True),
    ("p", "Mã nguồn: https://github.com/BinhTHB/btl-kho-du-lieu.git (nhánh main)."),
    ("p", "Chạy ứng dụng: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 rồi mở http://127.0.0.1:8000; chạy Dagster tại http://127.0.0.1:3000. Sinh lại dữ liệu: python mockup_generator\\generate_sample_data.py. Kiểm tra: python -m app.selfcheck."),
    ("p", "Tài liệu liên quan: ssas/HUONG_DAN_SSAS_VA_EXCEL.md, sql/04_truy_van_minh_hoa.sql, sql/06_sqlserver_dw_and_indexed_views.sql và ssas/HocTapOLAP_Excel.xlsx."),
    ("p", "Báo cáo có tham khảo cách tổng hợp bảng biểu và trình bày sơ đồ kiến trúc, ERD, Fact – Dimension trong BTL Kho dữ liệu của Nhóm 5 cùng học phần (xem tài liệu tham khảo [10]). Số liệu và thiết kế trong báo cáo này vẫn là của Nhóm 9 trên tập Seed 9."),
]

# ---------------------------------------------------------------------------
# Tiện ích DOCX
# ---------------------------------------------------------------------------
def set_run_font(run, size=13, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        fonts.set(qn(attr), "Times New Roman")


def format_paragraph(paragraph, *, indent=True, center=False, bold=False, size=13, justify=True):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(3)
    fmt.space_after = Pt(4)
    fmt.line_spacing = 1.3
    fmt.first_line_indent = Cm(1 if indent and not bold and not center else 0)
    if center:
        fmt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif justify:
        fmt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for run in paragraph.runs:
        set_run_font(run, size=size, bold=bold)


def insert_after(paragraph, text="", *, bold=False, indent=True, center=False, size=13):
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    para = Paragraph(new_p, paragraph._parent)
    if text:
        run = para.add_run(text)
        set_run_font(run, size=size, bold=bold)
    format_paragraph(para, indent=indent, center=center, bold=bold, size=size)
    return para


def set_paragraph_text(paragraph, text, *, bold=False, size=13, center=False):
    if paragraph.runs:
        paragraph.runs[0].text = text
        for extra in paragraph.runs[1:]:
            extra.text = ""
        set_run_font(paragraph.runs[0], size=size, bold=bold)
    else:
        run = paragraph.add_run(text)
        set_run_font(run, size=size, bold=bold)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else paragraph.alignment
    paragraph.paragraph_format.first_line_indent = Cm(0)


def paint_cell(cell, text, bold=False, size=11):
    # Khung mẫu thường có nhiều đoạn trong một ô; xóa hết để không lẫn nội dung cũ
    for extra in cell.paragraphs[1:]:
        element = extra._element
        element.getparent().remove(element)
    paragraph = cell.paragraphs[0]
    if paragraph.runs:
        paragraph.runs[0].text = str(text)
        for extra in paragraph.runs[1:]:
            extra.text = ""
        set_run_font(paragraph.runs[0], size=size, bold=bold)
    else:
        run = paragraph.add_run(str(text))
        set_run_font(run, size=size, bold=bold)
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.line_spacing = 1.0
    # Căn trái cho bảng dễ đọc; tiêu đề bảng được in đậm
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def add_column(table):
    tbl = table._tbl
    grid = tbl.tblGrid
    cols = grid.findall(qn("w:gridCol"))
    grid.append(deepcopy(cols[-1]))
    for row in tbl.findall(qn("w:tr")):
        cells = row.findall(qn("w:tc"))
        row.append(deepcopy(cells[-1]))


def style_headings(doc):
    for name, size in (("Heading 1", 14), ("Heading 2", 13), ("Heading 3", 13)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.line_spacing = 1.3
        style.paragraph_format.first_line_indent = Cm(0)
    for name in ("Normal", "List Paragraph"):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(13)
        style.paragraph_format.line_spacing = 1.3


def enable_field_update(doc):
    settings = doc.settings.element
    for tag in ("w:updateFields",):
        old = settings.find(qn(tag))
        if old is not None:
            settings.remove(old)
    node = OxmlElement("w:updateFields")
    node.set(qn("w:val"), "true")
    settings.append(node)


def insert_toc_field(doc, paragraph):
    """Chèn trường TOC tự động ngay sau một đoạn."""
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    para = Paragraph(new_p, paragraph._parent)
    para.paragraph_format.first_line_indent = Cm(0)
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(6)

    def field_run(kind, text=None):
        run = para.add_run()
        if text is not None:
            run.text = text
            set_run_font(run, size=11)
        node = OxmlElement("w:fldChar")
        node.set(qn("w:fldCharType"), kind)
        run._r.append(node)
        return run

    field_run("begin")
    run = para.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '
    run._r.append(instr)
    field_run("separate")
    run = para.add_run("Nhấn F9 để cập nhật mục lục.")
    set_run_font(run, size=11)
    field_run("end")
    return para


def add_table_after(paragraph, spec):
    caption = insert_after(paragraph, spec["caption"], bold=True, indent=False, center=True, size=12)
    table = paragraph.part.document.add_table(rows=1 + len(spec["rows"]), cols=len(spec["headers"]))
    try:
        table.style = "Table Grid"
    except KeyError:
        pass
    caption._p.addnext(table._tbl)
    for col, header in enumerate(spec["headers"]):
        paint_cell(table.rows[0].cells[col], header, bold=True, size=10)
    for r, row in enumerate(spec["rows"]):
        for c, value in enumerate(row):
            paint_cell(table.rows[r + 1].cells[c], value, bold=False, size=10)
    tail = OxmlElement("w:p")
    table._tbl.addnext(tail)
    return Paragraph(tail, paragraph._parent)


def add_figure_after(paragraph, image_path, caption, width_cm=12.5):
    pic_p = OxmlElement("w:p")
    paragraph._p.addnext(pic_p)
    pic_para = Paragraph(pic_p, paragraph._parent)
    pic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic_para.paragraph_format.first_line_indent = Cm(0)
    pic_para.paragraph_format.space_before = Pt(6)
    pic_para.paragraph_format.space_after = Pt(2)
    run = pic_para.add_run()
    run.add_picture(str(image_path), width=Cm(width_cm))
    cap = insert_after(pic_para, caption, bold=True, indent=False, center=True, size=12)
    return insert_after(cap, "Nguồn: Nhóm thực hiện", indent=False, center=True, size=10)


def cut_after(doc, start_text):
    body = doc.element.body
    start = None
    for child in list(body):
        if child.tag != qn("w:p"):
            continue
        text = "".join(node.text or "" for node in child.iter(qn("w:t"))).strip()
        if text.startswith(start_text):
            start = child
            break
    if start is None:
        raise SystemExit(f"Không thấy mốc '{start_text}' trong khung mẫu")
    removing = False
    for child in list(body):
        if child is start:
            removing = True
        if removing and child.tag != qn("w:sectPr"):
            body.remove(child)


def find_figure_file(info):
    folders = [SO_DO, HINH] if info.get("folder") == "so-do" else [HINH, SO_DO]
    for folder in folders:
        path = folder / info["file"]
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def heading(doc, text, level, newpage=False, after_element=None):
    if after_element is None:
        para = insert_after(doc._cursor, text, bold=True, indent=False,
                            center=(level == 1), size=14 if level == 1 else 13)
    else:
        # Chèn heading ngay sau một phần tử bảng (bỏ đoạn rỗng tail đi kèm).
        new_p = OxmlElement("w:p")
        after_element.addnext(new_p)
        para = Paragraph(new_p, doc._cursor._parent)
        run = para.add_run(text)
        set_run_font(run, size=14 if level == 1 else 13, bold=True)
        format_paragraph(para, indent=False, center=(level == 1), bold=True,
                         size=14 if level == 1 else 13)
    para.style = doc.styles["Heading 1" if level == 1 else "Heading 2"]
    para.paragraph_format.first_line_indent = Cm(0)
    if newpage:
        para.paragraph_format.page_break_before = True
    doc._cursor = para
    return para


def emit_block(doc, block):
    kind = block[0]
    if kind == "h1":
        newpage = bool(block[2]) if len(block) > 2 else False
        after_el = None
        if newpage:
            cur_el = doc._cursor._p
            prev_el = cur_el.getprevious()
            # Một bảng sinh ra đoạn rỗng "tail" ngay sau nó. Nếu heading có
            # page_break_before đứng ngay sau tail đó, tail bị đẩy sang trang mới
            # và để lại một trang trắng. Bỏ tail, đặt heading thẳng sau bảng.
            if (cur_el.tag == qn('w:p') and not ''.join(cur_el.itertext()).strip()
                    and prev_el is not None and prev_el.tag == qn('w:tbl')):
                after_el = prev_el
        para = heading(doc, block[1], 1, newpage=newpage, after_element=after_el)
        if after_el is not None:
            tail_el = para._p.getnext()
            if (tail_el is not None and tail_el.tag == qn('w:p')
                    and not ''.join(tail_el.itertext()).strip()):
                tail_el.getparent().remove(tail_el)
    elif kind == "h2":
        heading(doc, block[1], 2)
    elif kind == "p":
        doc._cursor = insert_after(doc._cursor, block[1])
    elif kind == "table":
        doc._cursor = add_table_after(doc._cursor, TABLES[block[1]])
    elif kind == "fig":
        key, width = block[1], block[2]
        info = FIGURES[key]
        path = find_figure_file(info)
        if path is not None:
            doc._cursor = add_figure_after(doc._cursor, path, info["caption"], width)
        else:
            print("Không chèn ảnh (file không tồn tại):", info["file"])
    elif kind == "ref":
        for text in REFERENCES:
            doc._cursor = insert_after(doc._cursor, text, indent=False)
    elif kind == "pagebreak":
        para = insert_after(doc._cursor, "", indent=False)
        para.runs and para.runs[0].add_break(WD_BREAK.PAGE)
        doc._cursor = para
    else:
        raise ValueError(f"Block không rõ: {kind}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not TEMPLATE.exists():
        raise SystemExit(f"Không thấy khung mẫu: {TEMPLATE}")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists():
        backup_docx(DEST)
    shutil.copy2(TEMPLATE, DEST)
    doc = Document(str(DEST))
    # Bỏ các đề mục rỗng có sẵn trong khung mẫu (chỉ là đoạn ngắt trang)
    for para in list(doc.paragraphs):
        if para.style.name.startswith("Heading") and not para.text.strip():
            element = para._element
            element.getparent().remove(element)
    style_headings(doc)
    enable_field_update(doc)

    # --- Bìa ---
    hoc_vien = next(p for p in doc.paragraphs if p.text.strip().startswith("HỌC VIỆN"))
    if not any(p.text.strip().startswith("BỘ THÔNG TIN") for p in doc.paragraphs):
        new_p = OxmlElement("w:p")
        hoc_vien._p.addprevious(new_p)
        first = Paragraph(new_p, hoc_vien._parent)
        run = first.add_run("BỘ THÔNG TIN VÀ TRUYỀN THÔNG")
        set_run_font(run, size=13, bold=True)
        first.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("TIỂU LUẬN"):
            set_paragraph_text(paragraph, "BÁO CÁO BÀI TẬP LỚN", bold=True, size=16, center=True)
        elif text.startswith("ĐỀ TÀI"):
            set_paragraph_text(paragraph, "ĐỀ TÀI: " + TEN_DE_TAI, bold=True, size=14, center=True)
        elif text.startswith("Hà Nội"):
            set_paragraph_text(paragraph, "Hà Nội, tháng 11 năm 2026", bold=True, size=13, center=True)

    bia = doc.tables[0]
    paint_cell(bia.rows[0].cells[2], GVHD, size=11)
    paint_cell(bia.rows[1].cells[2], "Nhóm 9 – Hệ thống Quản lý Học tập và Ôn luyện Trực tuyến", size=11)
    paint_cell(bia.rows[2].cells[2], LOP, size=11)
    if len(bia.rows) < 7:
        bia.add_row()
    for i, (name, mssv, _role, _work) in enumerate(THANH_VIEN):
        paint_cell(bia.rows[3 + i].cells[2], f"{name} – {mssv}", size=11)

    # --- Phiếu phân công & đánh giá (dùng bảng có sẵn của template) ---
    viec = doc.tables[1]
    while len(viec.rows) < 1 + len(THANH_VIEN):
        viec.add_row()
    # Hàng 0 là tiêu đề có sẵn của khung mẫu, giữ nguyên
    for r, values in enumerate(TABLES["phan_cong"]["rows"], start=1):
        for c, value in enumerate(values):
            paint_cell(viec.rows[r].cells[c], value, bold=False, size=9)

    diem = doc.tables[2]
    if len(diem.columns) < 6:
        add_column(diem)
    for r, values in enumerate(TABLES["diem"]["rows"]):
        for c, value in enumerate(values):
            paint_cell(diem.rows[r].cells[c], value, bold=(r == 0), size=10)
    for r in range(len(TABLES["diem"]["rows"]), len(diem.rows)):
        tr = diem.rows[r]._tr
        tr.getparent().remove(tr)

    for paragraph in doc.paragraphs:
        if paragraph.text.strip().startswith("Trong quá trình thực hiện"):
            set_paragraph_text(
                paragraph,
                "Trong quá trình thực hiện bài tập lớn, các thành viên hoàn thành đúng phần việc đã phân công: "
                "kiến trúc kho và SCD, triển khai SQL Server cùng khối SSAS, nguồn OLTP cùng hai cổng web, "
                "tầng tổng hợp và báo cáo. Mốc đối soát dùng chung là 344 lần nộp, 822 phiên học và 51 phiên bản học sinh. "
                "Nhóm trưởng xác nhận bảng điểm theo trọng số 50%, 30% và 20%.",
            )

    # --- Xóa thân bài cũ của khung mẫu ---
    cut_after(doc, "DANH MỤC THUẬT NGỮ")
    anchor = next(p for p in doc.paragraphs if "Ký tên" in p.text)
    # Khung mẫu còn một bản Mục lục cũ (có cả cached entries) bị đẩy xuống cuối;
    # xóa mọi đoạn mang kiểu TOC trước khi chèn bản Mục lục mới.
    for para in list(doc.paragraphs):
        if para.style.name.startswith("TOC"):
            element = para._element
            element.getparent().remove(element)
    # Bản Mục lục cũ của khung mẫu nằm trong một khung nội dung (w:sdt)
    body = doc.element.body
    for sdt in list(body.findall(qn("w:sdt"))):
        instr = sdt.findall(".//" + qn("w:instrText"))
        if any("TOC" in (node.text or "") for node in instr):
            body.remove(sdt)
    doc._cursor = anchor

    # --- Mục lục tự động ---
    toc_title = insert_after(anchor, "MỤC LỤC", bold=True, indent=False, center=True, size=14)
    toc_title.style = doc.styles["Heading 1"]
    toc_title.paragraph_format.page_break_before = True
    doc._cursor = insert_toc_field(doc, toc_title)

    # --- Danh mục từ viết tắt / bảng / hình (sinh từ chính dữ liệu) ---
    heading(doc, "DANH MỤC TỰ VIẾT TẮT", 1)
    doc._cursor = add_table_after(doc._cursor, TABLES["abbr"])

    heading(doc, "DANH MỤC BẢNG", 1)
    danh_muc_bang = ["phan_cong", "diem"]
    danh_muc_bang += [b[1] for b in BLOCKS if b[0] == "table"]
    for key in danh_muc_bang:
        doc._cursor = insert_after(doc._cursor, TABLES[key]["caption"], indent=False)

    heading(doc, "DANH MỤC HÌNH VẼ", 1)
    for block in BLOCKS:
        if block[0] == "fig":
            info = FIGURES[block[1]]
            if find_figure_file(info) is not None:
                doc._cursor = insert_after(doc._cursor, info["caption"], indent=False)

    # --- Thân bài ---
    for block in BLOCKS:
        emit_block(doc, block)

    doc.save(str(DEST))
    print("Đã ghi", DEST)
    print("Tổng block:", len(BLOCKS))


if __name__ == "__main__":
    main()
