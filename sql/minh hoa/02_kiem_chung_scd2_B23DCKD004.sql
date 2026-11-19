USE DW_QuanLyHocTap;
GO

-- ==========================================================================================
-- BÀI TẬP LỚN KHO DỮ LIỆU - DEMO 02: KIỂM CHỨNG LỊCH SỬ THAY ĐỔI CHIỀU CHẬM (SCD TYPE 2)
-- Sinh viên kiểm chứng: B23DCKD004 (Nguyễn Quý Tường Anh) chuyển lớp ngày 12/10/2026
-- Hướng dẫn: Mở file trên SSMS và nhấn F5 để thực thi toàn bộ script.
-- ==========================================================================================

-- 1. TRUY VẤN LỊCH SỬ THAY ĐỔI CỦA SINH VIÊN B23DCKD004 TRÊN VIEW SCD
-- Kết quả kỳ vọng: 2 phiên bản (Version 1: Lớp D23CQKD03, Is_Current = 0; Version 2: Lớp D23CQCN01, Is_Current = 1)
SELECT
    HocSinhKey,
    MaHocSinh,
    HoTen,
    Lop,
    TrangThaiHocVu,
    LyDo,
    Start_Date,
    End_Date,
    Is_Current,
    VersionNo
FROM dbo.vw_dim_hoc_sinh_scd
WHERE MaHocSinh = N'B23DCKD004'
ORDER BY VersionNo ASC;
GO

-- 2. TRUY VẤN FACT BÀI THI CỦA B23DCKD004 THEO TIẾN TRÌNH THỜI GIAN
-- Mục đích: Chứng minh Fact gắn đúng Surrogate Key tương ứng tại thời điểm diễn ra sự kiện:
-- - Trước 12/10/2026: Dùng HocSinhKey = 1 (Lớp cũ D23CQKD03, Version 1)
-- - Từ 12/10/2026 trở đi: Dùng HocSinhKey = 49 (Lớp mới D23CQCN01, Version 2)
SELECT
    f.lan_lam_id,
    h.ma_hoc_sinh,
    h.ho_ten,
    f.hoc_sinh_key,
    h.version_no,
    h.lop AS lop_tai_thoi_diem_thi,
    t.ngay AS ngay_lam_bai,
    m.ma_mon,
    m.ten_mon,
    f.diem_so,
    f.loai_bai,
    CASE 
        WHEN t.ngay < '2026-10-12' THEN N'Trước chuyển lớp -> Khóa cũ (v1)'
        ELSE N'Sau chuyển lớp -> Khóa mới (v2)'
    END AS giai_doan_scd
FROM dbo.fact_ket_qua_thi AS f
INNER JOIN dbo.dim_hoc_sinh AS h ON f.hoc_sinh_key = h.hoc_sinh_key
INNER JOIN dbo.dim_thoi_gian AS t ON f.date_key = t.date_key
INNER JOIN dbo.dim_mon_hoc AS m ON f.mon_hoc_key = m.mon_hoc_key
WHERE h.ma_hoc_sinh = N'B23DCKD004'
ORDER BY t.ngay ASC;
GO
