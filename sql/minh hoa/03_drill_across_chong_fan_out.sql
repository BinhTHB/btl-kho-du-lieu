USE DW_QuanLyHocTap;
GO

-- ==========================================================================================
-- BÀI TẬP LỚN KHO DỮ LIỆU - DEMO 03: DRILL-ACROSS VÀ GIẢI PHÁP CHỐNG BẪY NHÂN BẢN DỮ LIỆU (FAN-OUT)
-- Đối tượng kiểm chứng: Sinh viên B23DCKD004, Môn học CSDL
-- Hướng dẫn: Mở file trên SSMS và nhấn F5 để thực thi toàn bộ script.
-- ==========================================================================================

-- 3A. TRUY VẤN CHUẨN QUA VIEW DRILL-ACROSS (TỔNG HỢP RIÊNG RỒI FULL OUTER JOIN)
-- Kết quả chuẩn: 5 lượt thi, tổng 26 điểm (TB: 5.2), 7 phiên học, tổng 110.55 phút (TB điểm CC: 5.67)
SELECT
    ma_hoc_sinh,
    ho_ten,
    lop_hien_tai,
    ma_mon,
    ten_mon,
    so_luot_thi,
    diem_tb,
    so_phien,
    tong_phut,
    diem_cc
FROM dbo.vw_drill_across
WHERE ma_hoc_sinh = N'B23DCKD004' AND ma_mon = N'CSDL';
GO

-- 3B. TRUY VẤN ĐỐI CHỨNG: BẪY FAN-OUT KHI JOIN TRỰC TIẾP 2 FACT
-- Sai lầm thường gặp: JOIN 2 bảng Fact có độ hạt khác nhau (5 bài thi x 7 phiên học = 35 dòng)
-- Dẫn đến tổng điểm bị thổi phồng thành 182 (26 * 7) và tổng phút bị thổi phồng thành 552.75 (110.55 * 5)
SELECT
    COUNT(*) AS so_dong_bi_nhan_ban,
    SUM(f.diem_so) AS tong_diem_bi_thoi_phong,
    SUM(c.thoi_luong_phut) AS tong_phut_bi_thoi_phong,
    N'Bẫy Fan-Out do JOIN trực tiếp 2 Fact (5 bài thi x 7 phiên = 35 dòng)' AS canh_bao
FROM dbo.fact_ket_qua_thi AS f
INNER JOIN dbo.fact_chuyen_can AS c ON f.mon_hoc_key = c.mon_hoc_key
INNER JOIN dbo.dim_hoc_sinh AS h1 ON f.hoc_sinh_key = h1.hoc_sinh_key
INNER JOIN dbo.dim_hoc_sinh AS h2 ON c.hoc_sinh_key = h2.hoc_sinh_key
INNER JOIN dbo.dim_mon_hoc AS m ON f.mon_hoc_key = m.mon_hoc_key
WHERE h1.ma_hoc_sinh = N'B23DCKD004'
  AND h2.ma_hoc_sinh = N'B23DCKD004'
  AND m.ma_mon = N'CSDL';
GO

-- 3C. THỐNG KÊ TỔNG THỂ CÁC CẶP SINH VIÊN X MÔN HỌC TRÊN TOÀN BỘ KHO DỮ LIỆU
-- Cho thấy sức mạnh của FULL OUTER JOIN trong kiến trúc Drill-Across (không bỏ sót bất kỳ luồng nào)
SELECT
    CASE 
        WHEN so_luot_thi IS NOT NULL AND so_phien IS NOT NULL THEN N'1. Có cả Điểm thi & Chuyên cần'
        WHEN so_luot_thi IS NOT NULL AND so_phien IS NULL THEN N'2. Chỉ có Điểm thi (Không học LMS)'
        WHEN so_luot_thi IS NULL AND so_phien IS NOT NULL THEN N'3. Chỉ có Chuyên cần (Chưa thi)'
    END AS phan_loai,
    COUNT(*) AS so_luong_cap_sv_mon
FROM dbo.vw_drill_across
GROUP BY 
    CASE 
        WHEN so_luot_thi IS NOT NULL AND so_phien IS NOT NULL THEN N'1. Có cả Điểm thi & Chuyên cần'
        WHEN so_luot_thi IS NOT NULL AND so_phien IS NULL THEN N'2. Chỉ có Điểm thi (Không học LMS)'
        WHEN so_luot_thi IS NULL AND so_phien IS NOT NULL THEN N'3. Chỉ có Chuyên cần (Chưa thi)'
    END
ORDER BY phan_loai;
GO
