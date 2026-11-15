# LearnWH — Kho học tập và ôn luyện trực tuyến

Bài tập lớn môn Kho dữ liệu (DAE1408), Nhóm 9, lớp D23CQKD02-B. Hệ quản trị là Microsoft SQL Server (`MSSQLSERVER`, kết nối mặc định `localhost` bằng **Windows Authentication**). Web App chỉ ghi OLTP và đọc DW; ETL chạy native trên Windows qua **Dagster**.

## Chạy trên Windows (2 terminal)

1. Đảm bảo `SQL Server (MSSQLSERVER)` và `SQL Server Analysis Services (MSSQLSERVER)` đang `Running` trong `services.msc`.
2. Cài thư viện:
   ```bat
   python -m pip install -r requirements.txt
   ```
3. Nạp dữ liệu mẫu ban đầu (nếu chưa có):
   ```bat
   python mockup_generator\generate_sample_data.py
   ```
4. Mở Terminal 1 chạy Web App:
   ```bat
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
5. Mở Terminal 2 chạy Dagster Web UI:
   - **Command Prompt (cmd):**
     ```bat
     if not exist .dagster_home mkdir .dagster_home
     set DAGSTER_HOME=%CD%\.dagster_home && dagster dev -f orchestration/etl_assets.py -p 3000
     ```
   - **PowerShell:**
     ```powershell
     New-Item -ItemType Directory -Force .dagster_home | Out-Null
     $env:DAGSTER_HOME = "$PWD\.dagster_home"
     dagster dev -f orchestration/etl_assets.py -p 3000
     ```
6. Mở trình duyệt:
   - Web App: http://127.0.0.1:8000
   - Dagster UI (cây Assets Lineage, bấm **Materialize all**): http://127.0.0.1:3000

> `.dagster_home/` được bỏ qua trong git. Kết nối mặc định dùng Windows Auth (`Trusted_Connection`) tới `localhost`; có thể ghi đè bằng `MSSQL_SERVER`, `MSSQL_USER`, `MSSQL_PASSWORD`, `ODBC_DRIVER` nếu cần.

## Luồng dữ liệu và ETL (Dagster Assets)

- Web App ghi vào `OLTP_QuanLyHocTap`; Dashboard đọc indexed view của `DW_QuanLyHocTap`. Không có ETL chạy ngầm trong FastAPI.
- Pipeline `orchestration/etl_assets.py` (lịch `*/2 * * * *`): `oltp_extracted_batch` → `quality_gate_checked` → `dim_hoc_sinh_scd2` → `dw_fact_tables` → `dw_audit_and_summary` (đối soát `Nguon = Nap + Loai`, dọn staging).
- 5 bước ETL trong `app/etl.py`: `step_extract`, `step_quality_gate`, `step_scd2`, `step_load_facts`, `step_audit` (giữ nguyên `run_batch` cho `selfcheck`/generator).

## Bố cục đúng yêu cầu môn

- OLTP: học sinh, môn, đề, câu hỏi, bài học, lần làm bài, phiên học, sự kiện học vụ.
- Hai fact độc lập: `fact_ket_qua_thi` (một lần nộp) và `fact_chuyen_can` (một phiên học).
- Chiều dùng chung: thời gian, học sinh, môn. Chiều riêng: đề thi và bài học.
- SCD Type 2 trên học sinh: `start_date`, `end_date`, `is_current`. Xem view `vw_dim_hoc_sinh_scd`.
- Mã lạ nhận khóa -1, không làm rơi fact.
- Cổng chất lượng loại điểm, số câu, thời lượng vô lý. Bảng `etl_batch` đối soát số dòng nguồn = nạp + loại.
- Tầng tổng hợp là indexed view `iv_diem_theo_mon_thang` và `iv_chuyen_can_theo_lop_tuan`. Dashboard đọc view bằng `WITH (NOEXPAND)`.
- Bản dựng lại trong SSMS là `sql/06_sqlserver_dw_and_indexed_views.sql`. Hướng dẫn SSDT và Excel: `ssas/HUONG_DAN_SSAS_VA_EXCEL.md`.
- OLAP: Roll-up, Drill-down, Slice, Dice, Pivot. Drill-across gộp từng fact rồi `FULL OUTER JOIN`.

## Kiểm thử

```bat
python -m app.selfcheck
python mockup_generator\generate_sample_data.py
dagster asset materialize --select * -f orchestration/etl_assets.py
```

Câu SQL mở tay nằm ở `sql/04_truy_van_minh_hoa.sql`. Bản thảo báo cáo là `Bao_cao_BTL_Kho_du_lieu_Nhom9.docx` ở thư mục này.

