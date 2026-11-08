# LearnWH — Kho học tập và ôn luyện trực tuyến

Bài tập lớn môn Kho dữ liệu (DAE1408), Nhóm 9, lớp D23CQKD02-B. Hệ quản trị là Microsoft SQL Server. Máy này dùng LocalDB `(localdb)\MSSQLLocalDB` khi không đặt `MSSQL_SERVER`.

## Chạy

```bat
python -m pip install -r requirements.txt
python mockup_generator\generate_sample_data.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở http://127.0.0.1:8000

Script mẫu nạp 344 bài thi, 822 phiên học và các sự kiện chuyển lớp vào `OLTP_QuanLyHocTap`, rồi ETL ghi sang `DW_QuanLyHocTap`. Ứng dụng không tự sinh dữ liệu khi khởi động. Cổng học sinh ghi vào OLTP. Dashboard đọc indexed view của kho.

## Bố cục đúng yêu cầu môn

- OLTP: học sinh, môn, đề, câu hỏi, bài học, lần làm bài, phiên học, sự kiện học vụ.
- Hai fact độc lập: `fact_ket_qua_thi` (một lần nộp) và `fact_chuyen_can` (một phiên học).
- Chiều dùng chung: thời gian, học sinh, môn. Chiều riêng: đề thi và bài học.
- SCD Type 2 trên học sinh: `start_date`, `end_date`, `is_current`. Xem view `vw_dim_hoc_sinh_scd`.
- Mã lạ nhận khóa -1, không làm rơi fact.
- Cổng chất lượng loại điểm, số câu, thời lượng vô lý. Bảng `etl_batch` đối soát số dòng nguồn = nạp + loại.
- Tầng tổng hợp là indexed view `iv_diem_theo_mon_thang` và `iv_chuyen_can_theo_lop_tuan`. Dashboard đọc view bằng `WITH (NOEXPAND)`.
- Bản dựng lại trong SSMS là `sql/06_sqlserver_dw_and_indexed_views.sql`. Sau đó chạy `python mockup_generator\generate_sample_data.py`. Hướng dẫn SSDT và Excel: `ssas/HUONG_DAN_SSAS_VA_EXCEL.md`.
- Đổi instance bằng biến `MSSQL_SERVER`. Mặc định là `(localdb)\MSSQLLocalDB`, ODBC Driver 17, đăng nhập Windows.
- OLAP: Roll-up, Drill-down, Slice, Dice, Pivot. Drill-across gộp từng fact rồi `FULL OUTER JOIN`.

## Khi bảo vệ

1. Bảng điều khiển: dải số từ OLTP tới summary.
2. Cổng học tập: chọn thành viên nhóm, nộp một đề hoặc ghi một phiên học.
3. Học vụ: đổi lớp hoặc trạng thái, đối chiếu Start_Date / End_Date và khóa trên các bài cũ.
4. Dòng dữ liệu: bật bộ sinh, chạy kịch bản end-to-end, bơm một bài bẩn.
5. OLAP: bấm năm nút thao tác, rồi Drill-across để thấy ô trống và ví dụ số bị nhân nếu join thẳng hai fact.
6. Chất lượng ETL: bảng đối soát nguồn = nạp + loại, và hàng bị loại.

Câu SQL mở tay nằm ở `sql/04_truy_van_minh_hoa.sql`. Kiểm tra logic không cần mở web: `python -m app.selfcheck`.

Bản thảo báo cáo (khung PTIT, trích dẫn IEEE, tối đa 30 trang) là `Bao_cao_BTL_Kho_du_lieu_Nhom9.docx` ở thư mục này. Số liệu trong bản thảo lấy từ mẻ khởi tạo sạch: 344 bài, 822 phiên, 51 phiên bản SCD.
