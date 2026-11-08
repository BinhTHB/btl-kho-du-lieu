-- Đối chiếu cú pháp CREATE MATERIALIZED VIEW trên PostgreSQL.
-- Kho phòng lab dùng indexed view trong sql/06_sqlserver_dw_and_indexed_views.sql.

CREATE MATERIALIZED VIEW mv_diem_theo_mon_thang AS
SELECT
    t.nam,
    t.thang,
    t.hoc_ky,
    t.nam_hoc,
    m.mon_hoc_key,
    m.ten_mon,
    h.lop,
    f.loai_bai,
    COUNT(*) AS so_luot,
    SUM(f.diem_so) AS tong_diem,
    ROUND(AVG(f.diem_so)::numeric, 2) AS diem_tb,
    SUM(f.so_cau_dung) AS tong_cau_dung,
    SUM(f.tong_so_cau) AS tong_cau,
    ROUND((SUM(f.so_cau_dung)::numeric / NULLIF(SUM(f.tong_so_cau), 0)), 4) AS ty_le_dung,
    SUM(f.thoi_gian_lam_giay) AS tong_giay
FROM fact_ket_qua_thi f
JOIN dim_thoi_gian t ON t.date_key = f.date_key
JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
WHERE f.date_key > 0
GROUP BY t.nam, t.thang, t.hoc_ky, t.nam_hoc, m.mon_hoc_key, m.ten_mon, h.lop, f.loai_bai
WITH DATA;

CREATE UNIQUE INDEX ux_mv_diem
    ON mv_diem_theo_mon_thang (nam, thang, mon_hoc_key, lop, loai_bai);

-- Làm mới sau mỗi mẻ ETL. CONCURRENTLY cần unique index ở trên.
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_diem_theo_mon_thang;

-- Bitmap index là kỹ thuật Oracle cho cột ít giá trị (loai_bai, loai_noi_dung).
-- PostgreSQL không tạo bitmap index lưu sẵn; planner có thể bitmap-scan trên B-Tree.
-- CREATE INDEX ix_fact_exam_loai ON fact_ket_qua_thi (loai_bai);
-- Ví dụ Oracle, chỉ để đối chiếu giáo trình:
-- CREATE BITMAP INDEX bix_fact_exam_loai ON fact_ket_qua_thi (loai_bai);
