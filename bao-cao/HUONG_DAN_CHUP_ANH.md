# Hướng dẫn chụp ảnh cho bản thảo

Script `bao-cao/xay_dung_bao_cao.py` chỉ chèn ảnh có thật trong `bao-cao/hinh/`. Không vẽ sơ đồ bằng matplotlib. Ảnh thiếu thì chương đó bỏ trống chỗ hình và in tên file còn thiếu trên màn hình console.

Sau khi thả đúng tên file, chạy lại:

```bat
python bao-cao\xay_dung_bao_cao.py
```

Phím chụp vùng trên Windows: **Win + Shift + S**, chọn vùng, rồi dán vào Paint và lưu PNG đúng tên dưới đây. Nền trắng, không để thanh tác vụ che bảng.

## Ảnh giao diện web

Các file này được chụp từ http://127.0.0.1:8000 khi hệ thống đang chạy. Nếu cần chụp lại:

1. Chạy `run.bat`.
2. Mở trình duyệt, phóng to cửa sổ khoảng 1400 px.
3. Chụp cả thẻ nội dung, kể cả sidebar nếu còn chỗ.

| File | Màn hình | Chú thích trong báo cáo |
|---|---|---|
| `hinh_3_1_dashboard.png` | Bảng điều khiển: dải OLTP → fact → summary và biểu đồ theo môn | Hình 3.1 |
| `hinh_3_2_lam_de.png` | Cổng học tập, một đề đang mở, chưa cần nộp | Hình 3.2 |
| `hinh_3_3_scd.png` | Học vụ · SCD, học sinh `B23DCKD004`, thấy hai phiên bản Start_Date / End_Date / Is_Current | Hình 3.3 |
| `hinh_4_1_drill_across.png` | OLAP, đã bấm Drill-across, thấy bảng và dòng giải thích 5 × 7 | Hình 4.1 |

## Sơ đồ thiết kế

Mã nguồn sơ đồ nằm ở:

- `bao-cao/so-do/kien_truc.drawio`
- `bao-cao/so-do/chom_sao.drawio`

Mở bằng [diagrams.net](https://app.diagrams.net) hoặc Draw.io Desktop.

1. File → Open → chọn file `.drawio`.
2. File → Export as → PNG.
3. Zoom 200%, nền trắng, bỏ chọn “Shadow” nếu có.
4. Lưu đúng tên vào `bao-cao/hinh/`.

| File xuất | Sơ đồ | Chú thích |
|---|---|---|
| `hinh_2_1_kien_truc.png` | `kien_truc.drawio` | Hình 2.1: Sơ đồ kiến trúc tổng thể hệ thống |
| `hinh_2_2_chom_sao.png` | `chom_sao.drawio` | Hình 2.2: Lược đồ hình chòm sao của hai fact và các chiều |

Hai fact ở giữa. Ba chiều dùng chung ở trên. `dim_de_thi` chỉ nối fact kết quả. `dim_bai_hoc` chỉ nối fact chuyên cần. Không kéo mũi tên giữa hai fact.

## SQL Server Management Studio

File: `bao-cao/hinh/hinh_4_2_ssms_query.png`  
Tên cũ cũng được nhận: `hinh_4_1_ssms_query.png`.  
Chú thích: Hình 4.2: Kết quả drill-across trên SQL Server.

1. Chạy `sql/06_sqlserver_dw_and_indexed_views.sql`, rồi `sql/07_sqlserver_seed_data.sql`.
2. Bôi đen và chạy, database `DW_QuanLyHocTap`:

```sql
SELECT ma_hoc_sinh, ten_mon, so_luot_thi, diem_tb, so_phien, tong_phut
FROM dbo.vw_drill_across
WHERE ma_hoc_sinh = N'B23DCKD004' AND ma_mon = N'CSDL';
```

3. Chụp cửa sổ kết quả kèm câu lệnh. Phải thấy 5 lượt thi, tổng điểm suy ra 26, 7 phiên và 110,5 phút. Không chụp câu `JOIN` thẳng hai fact.
4. Có thể chụp thêm lưới kết quả của:

```sql
SELECT COUNT(*) AS so_bai FROM dbo.fact_ket_qua_thi;
SELECT COUNT(*) AS so_phien FROM dbo.fact_chuyen_can;
SELECT COUNT(*) AS so_phien_ban FROM dbo.dim_hoc_sinh WHERE hoc_sinh_key > 0;
```

Ba số 344, 822 và 51 nên nằm trong cùng một ảnh hoặc ảnh kế bên, miễn là file lưu đúng tên ở trên.

## Visual Studio SSDT

File: `bao-cao/hinh/hinh_4_3_ssas_dsv.png`  
Tên cũ cũng được nhận: `hinh_4_2_ssas_dsv.png`.  
Chú thích: Hình 4.3: Data Source View và hierarchy của khối SSAS.

Làm theo `ssas/HUONG_DAN_SSAS_VA_EXCEL.md` đến bước Data Source View.

1. Mở diagram DSV. Phải thấy `fact_ket_qua_thi`, `fact_chuyen_can` và năm chiều. Không có đường nối giữa hai fact.
2. Win + Shift + S, khoanh vùng diagram.
3. Nếu một ảnh chưa đủ hierarchy, chụp thêm khung dimension `dim_thoi_gian` đang mở hierarchy Năm học → Học kỳ → Tháng → Ngày, rồi ghép vào cùng file PNG trước khi lưu.

Sau khi đủ file, chạy lại script dựng báo cáo. Bản Word mới nằm ở `Bao_cao_BTL_Kho_du_lieu_Nhom9.docx`.
