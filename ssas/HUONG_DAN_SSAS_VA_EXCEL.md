# Hướng dẫn dựng khối SSAS và Excel PivotTable

Tài liệu này dùng cho phòng lab có SQL Server (SSMS), Visual Studio SSDT (Analysis Services Multidimensional) và Excel. Web app là cổng tác nghiệp và máy ETL. Kho mà khối đọc là `DW_QuanLyHocTap`.

## 1. Chuẩn bị kho trên SQL Server

1. Mở SSMS, kết nối instance local.
2. Mở và chạy `sql/06_sqlserver_dw_and_indexed_views.sql`. File tạo `OLTP_QuanLyHocTap` và `DW_QuanLyHocTap`, collation `Vietnamese_CI_AS`, năm chiều, hai fact, unknown member khóa `-1`, nonclustered index trên khóa ngoại và hai indexed view.
3. Tại thư mục dự án chạy:

```bat
python mockup_generator\generate_sample_data.py
```

Script nối `(localdb)\MSSQLLocalDB` (hoặc `MSSQL_SERVER` nếu đã đặt), nạp OLTP rồi ETL sang kho. Đối soát phải là 344 bài, 822 phiên, 51 phiên bản học sinh.
4. Chạy thử, vẫn trong `DW_QuanLyHocTap`:

```sql
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SELECT * FROM dbo.vw_diem_theo_mon_thang;
SELECT * FROM dbo.vw_drill_across WHERE ma_hoc_sinh = N'B23DCKD004';
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
```

`iv_diem_theo_mon_thang` và `iv_chuyen_can_theo_lop_tuan` là indexed view (`WITH SCHEMABINDING` và unique clustered index). `vw_drill_across` là view thường vì indexed view không nhận `FULL OUTER JOIN`.

## 2. Đồng bộ khi nộp bài trên web

Web và ETL nối thẳng SQL Server qua pyodbc, ODBC Driver 17. Mặc định là `(localdb)\MSSQLLocalDB`. Instance khác đặt bằng biến `MSSQL_SERVER`. Bài nộp trên cổng học sinh ghi vào `OLTP_QuanLyHocTap`; mẻ ETL đưa sang `DW_QuanLyHocTap`. Không có bản SQLite song song.

## 3. Tạo project SSAS trong Visual Studio

1. Visual Studio: **Create a new project** → **Analysis Services Multidimensional and Data Mining Project**. Đặt tên `HocTapOLAP`.
2. Solution Explorer → **Data Sources** → New. Provider **Microsoft OLE DB Driver for SQL Server** (hoặc SQL Server Native Client). Server là instance vừa chạy SSMS. Database `DW_QuanLyHocTap`. Impersonation: **Use the service account** nếu service SSAS đọc được database, hoặc **Inherit** kèm tài khoản Windows có quyền đọc.
3. **Data Source Views** → New → chọn data source vừa tạo. Chọn đúng bảy bảng:
   - Fact: `fact_ket_qua_thi`, `fact_chuyen_can`
   - Dimension: `dim_thoi_gian`, `dim_hoc_sinh`, `dim_mon_hoc`, `dim_de_thi`, `dim_bai_hoc`
4. Trong DSV, kiểm tra quan hệ:
   - `fact_ket_qua_thi.hoc_sinh_key` → `dim_hoc_sinh.hoc_sinh_key`
   - `fact_ket_qua_thi.date_key` → `dim_thoi_gian.date_key`
   - `fact_ket_qua_thi.mon_hoc_key` → `dim_mon_hoc.mon_hoc_key`
   - `fact_ket_qua_thi.de_thi_key` → `dim_de_thi.de_thi_key`
   - `fact_chuyen_can` nối học sinh, thời gian, môn và `bai_hoc_key` → `dim_bai_hoc.bai_hoc_key`
5. Không kéo quan hệ giữa hai bảng fact.

## 4. Dimension và hierarchy

Tạo năm dimension từ DSV. Khóa là surrogate key, không dùng mã nghiệp vụ làm key của chiều học sinh vì SCD Type 2 có nhiều dòng cùng `ma_hoc_sinh`.

**Thời gian** (`dim_thoi_gian`, key `date_key`):

- Attribute: `nam_hoc`, `hoc_ky`, `thang` (NameColumn `ten_thang` nếu muốn thấy “Tháng 9”), `ngay`.
- Hierarchy `H_ThoiGian`: Năm học → Học kỳ → Tháng → Ngày.
- Attribute relationships theo đúng thứ tự đó.

**Học sinh** (`dim_hoc_sinh`, key `hoc_sinh_key`):

- Attribute: `lop`, `trang_thai_hoc_vu`, `ho_ten`. Giữ `ma_hoc_sinh`, `Start_Date`/`start_date`, `end_date`, `is_current` làm attribute thường để lọc bản hiện tại khi cần.
- Hierarchy `H_HocSinh`: Lớp → Trạng thái → Học sinh.
- Vì SCD Type 2, một học sinh có nhiều key. Fact cũ trỏ key cũ nên Pivot theo lớp của key đó ra đúng lớp tại thời điểm nộp, không phải lớp hiện tại.

**Môn học** (`dim_mon_hoc`, key `mon_hoc_key`):

- Hierarchy `H_HocThuat`: Khoa (`khoa`) → Môn (`ten_mon`).

**Đề thi** (`dim_de_thi`, key `de_thi_key`):

- Hierarchy `H_DeThi`: Môn (`ma_mon`) → Đề (`ten_de`).

**Bài học** (`dim_bai_hoc`, key `bai_hoc_key`):

- Hierarchy `H_BaiHoc`: Môn (`ma_mon`) → Bài (`ten_bai`).

Ba hierarchy học thuật tách trên ba chiều vì đề và bài không nằm trong `dim_mon_hoc`. Trên Excel, người dùng lần từ Khoa → Môn, rồi mở chiều đề hoặc chiều bài.

## 5. Cube, measure và phân vùng

1. **Cube** → New. Measure group **Ket qua thi** từ `fact_ket_qua_thi`. Measure group **Chuyen can** từ `fact_chuyen_can`.
2. Measure nên để:
   - Kết quả: `diem_so` kiểu AverageOfChildren hoặc Average, `so_cau_dung` Sum, `tong_so_cau` Sum, `Fact Ket Qua Thi Count`.
   - Chuyên cần: `thoi_luong_phut` Sum, `so_video_da_xem` Sum, `diem_chuyen_can` Average, `Fact Chuyen Can Count`.
3. Gắn cả năm dimension vào cube. `dim_de_thi` chỉ measure group kết quả. `dim_bai_hoc` chỉ measure group chuyên cần. Ba chiều thời gian, học sinh, môn gắn cả hai measure group. Đây là conformed dimension.
4. Với mỗi partition MOLAP, mở **Storage Settings** và bật **Proactive Caching**, silence interval khoảng 10 giây, đưa về MOLAP. Sau khi web đẩy dòng mới vào SQL Server, khối tự process phần thay đổi. Excel bấm Refresh để đọc khối mới.
5. **Build** rồi **Deploy**. Trong tab **Process**, chọn **Process Full** lần đầu.

## 6. Năm thao tác trên Excel PivotTable

1. Excel → Data → Get Data → From Database → From Analysis Services. Server là instance SSAS (thường cùng tên SQL Server hoặc `localhost`). Chọn cube `HocTapOLAP`.
2. **Roll-up.** Kéo hierarchy `H_ThoiGian` vào Rows, chỉ để mức Năm học và Học kỳ. Values: số lượt bài và điểm trung bình. Học kỳ HK1 gộp các tháng.
3. **Drill-down.** Bấm dấu cộng tại HK1 để mở Tháng, rồi mở Ngày. Số lượt các tháng cộng lại bằng số lượt của học kỳ.
4. **Slice.** Kéo `ten_mon` vào Filters, chọn một môn, ví dụ Kho dữ liệu. Cả pivot chỉ còn môn đó.
5. **Dice.** Giữ filter môn, thêm filter `lop` = `D23CQKD03` và thu hẹp thời gian còn tháng 9 đến tháng 11. Ba điều kiện cùng lúc.
6. **Pivot.** Đưa `lop` xuống Rows, `ten_mon` sang Columns. Show Values As không bắt buộc. Đổi chỗ Rows với Columns để xoay cùng một khối.

Không kéo đồng thời số lượt của hai measure group vào một ô rồi nhân hai fact với nhau. Muốn đối soát điểm và phút, đặt hai value cạnh nhau sau khi đã lọc cùng lớp và cùng môn. Câu `vw_drill_across` trong SSMS là bản đối soát đúng hạt. Nối thẳng hai fact trong SQL sẽ ra 35 dòng cho Tường Anh môn Cơ sở dữ liệu, trong khi hạt đúng là 5 bài và 7 phiên.

## 7. Khi bảo vệ trên lab

1. Chạy web, mở dashboard, xác nhận 344 / 822 / 51.
2. SSMS: mở `vw_dim_hoc_sinh_scd`, lọc `MaHocSinh = B23DCKD004`, thấy hai phiên bản.
3. Visual Studio: Process Full nếu vừa nạp lại script 07.
4. Excel: làm lần lượt năm thao tác ở mục 6, rồi Refresh sau một bài nộp mới trên web để thấy proactive caching.
