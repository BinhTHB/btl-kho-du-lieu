-- Câu minh họa trên bản kho cục bộ. Bản T-SQL nằm ở sql/06_sqlserver_dw_and_indexed_views.sql.
-- sau khi hệ thống đã nạp dữ liệu. Không chạy file này lúc khởi tạo.

-- 1. Lịch sử SCD Type 2 của một học sinh
SELECT HocSinhKey, MaHocSinh, HoTen, Lop, TrangThaiHocVu, LyDo,
       Start_Date, End_Date, Is_Current, VersionNo
FROM vw_dim_hoc_sinh_scd
WHERE MaHocSinh = 'B23DCKD004'
ORDER BY VersionNo;

-- 2. Fact gắn đúng phiên bản tại thời điểm nộp bài, không lấy bản is_current.
SELECT t.ngay, f.diem_so, h.hoc_sinh_key, h.version_no, h.lop, h.start_date, h.end_date
FROM fact_ket_qua_thi f
JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
JOIN dim_thoi_gian t ON t.date_key = f.date_key
WHERE h.ma_hoc_sinh = 'B23DCKD004'
ORDER BY t.ngay;

-- 3. Drill-across: gộp từng fact trước, rồi FULL OUTER JOIN theo chiều dùng chung.
WITH diem AS (
    SELECT h.ma_hoc_sinh, m.ma_mon,
           ROUND(AVG(f.diem_so), 2) AS diem_tb,
           COUNT(*) AS so_luot_thi
    FROM fact_ket_qua_thi f
    JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
    JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
    GROUP BY h.ma_hoc_sinh, m.ma_mon
),
chuyen AS (
    SELECT h.ma_hoc_sinh, m.ma_mon,
           ROUND(SUM(f.thoi_luong_phut), 1) AS tong_phut,
           COUNT(*) AS so_phien
    FROM fact_chuyen_can f
    JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
    JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
    GROUP BY h.ma_hoc_sinh, m.ma_mon
)
SELECT COALESCE(d.ma_hoc_sinh, c.ma_hoc_sinh) AS ma_hoc_sinh,
       COALESCE(d.ma_mon, c.ma_mon) AS ma_mon,
       d.diem_tb, d.so_luot_thi, c.tong_phut, c.so_phien
FROM diem d
FULL OUTER JOIN chuyen c
  ON d.ma_hoc_sinh = c.ma_hoc_sinh AND d.ma_mon = c.ma_mon;

-- 4. Đối soát số dòng trước và sau ETL
SELECT trigger_name, src_exam, loaded_exam, rejected_exam,
       src_session, loaded_session, rejected_session, scd_new, status
FROM etl_batch
ORDER BY batch_id DESC;

-- 5. Hàng bị cổng chất lượng loại
SELECT nguon, nguon_id, ly_do, created_at FROM etl_reject ORDER BY id DESC;

-- 6. Kế hoạch dùng B-Tree trên khóa ngoại
EXPLAIN QUERY PLAN
SELECT * FROM fact_ket_qua_thi WHERE hoc_sinh_key = 1;
