-- ==========================================================================================
-- BÀI TẬP LỚN KHO DỮ LIỆU - DEMO 04: TỐI ƯU HIỆU NĂNG VỚI INDEXED VIEW (MATERIALIZED VIEW)
-- ==========================================================================================
-- HƯỚNG DẪN QUAN SÁT EXECUTION PLAN TRÊN SSMS:
--   1. Trên thanh công cụ SSMS, bật biểu tượng "Include Actual Execution Plan"
--      hoặc nhấn tổ hợp phím [Ctrl + M].
--   2. Nhấn [F5] để thực thi toàn bộ script.
--   3. Chuyển sang tab "Execution Plan" và tab "Messages" để so sánh:
--      - (4A) Quét trực tiếp Fact: tốn chi phí CPU, Hash Match / Aggregate, đọc nhiều Logical Reads.
--      - (4B) Đọc qua Indexed View WITH (NOEXPAND): chi phí cực nhỏ (chỉ 1 Clustered Index Scan).
-- ==========================================================================================

USE DW_QuanLyHocTap;
GO

SET STATISTICS IO, TIME ON;
GO

-- (4A) TRUY VẤN QUÉT TRỰC TIẾP FACT VÀ 3 BẢNG DIMENSION (CHƯA DÙNG VIEW VẬT LÝ HÓA)
-- Cần JOIN: fact_ket_qua_thi + dim_thoi_gian + dim_mon_hoc + dim_hoc_sinh
-- Cần GROUP BY và tính toán lại toàn bộ hàm tập hợp: COUNT_BIG, SUM.
SELECT
    t.nam,
    t.thang,
    m.ten_mon,
    h.lop,
    f.loai_bai,
    COUNT_BIG(*) AS so_luot,
    SUM(f.diem_so) AS tong_diem,
    SUM(f.so_cau_dung) AS tong_cau_dung,
    SUM(f.tong_so_cau) AS tong_cau,
    SUM(f.thoi_gian_lam_giay) AS tong_giay
FROM dbo.fact_ket_qua_thi AS f
INNER JOIN dbo.dim_thoi_gian AS t ON t.date_key = f.date_key
INNER JOIN dbo.dim_mon_hoc AS m ON m.mon_hoc_key = f.mon_hoc_key
INNER JOIN dbo.dim_hoc_sinh AS h ON h.hoc_sinh_key = f.hoc_sinh_key
WHERE f.date_key > 0
GROUP BY t.nam, t.thang, m.ten_mon, h.lop, f.loai_bai
ORDER BY t.nam, t.thang, m.ten_mon, h.lop, f.loai_bai;
GO

-- (4B) TRUY VẤN ĐỌC TRỰC TIẾP TỪ INDEXED VIEW VẬT LÝ HÓA VỚI HINT WITH (NOEXPAND)
-- Kết quả đã được tính sẵn và lưu trên đĩa theo Clustered Index:
-- ux_iv_diem_theo_mon_thang (nam, thang, mon_hoc_key, lop, loai_bai).
-- Không tốn chi phí tính toán lại, trả kết quả tức thì.
SELECT
    nam,
    thang,
    ten_mon,
    lop,
    loai_bai,
    so_luot,
    tong_diem,
    tong_cau_dung,
    tong_cau,
    tong_giay
FROM dbo.iv_diem_theo_mon_thang WITH (NOEXPAND)
ORDER BY nam, thang, ten_mon, lop, loai_bai;
GO

SET STATISTICS IO, TIME OFF;
GO
