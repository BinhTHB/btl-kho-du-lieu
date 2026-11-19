USE DW_QuanLyHocTap;
GO

-- ==========================================================================================
-- BÀI TẬP LỚN KHO DỮ LIỆU - DEMO 05: ĐỐI SOÁT ĐỘ LỆCH DỮ LIỆU GIỮA OLTP VÀ DATA WAREHOUSE
-- Chứng minh kiến trúc tách biệt OLTP và DW trước/sau khi ETL Dagster đồng bộ dữ liệu.
-- Hướng dẫn: Mở file trên SSMS và nhấn F5 để thực thi toàn bộ script.
-- ==========================================================================================

-- 1. BẢNG TỔNG HỢP SỐ LƯỢNG BẢN GHI ĐỐI ỨNG GIỮA TÁC NGHIỆP VÀ KHO DỮ LIỆU
SELECT
    N'OLTP' AS phan_he,
    N'OLTP_QuanLyHocTap.dbo.lan_lam_bai' AS ten_bang,
    N'Dữ liệu bài thi gốc từ ứng dụng tác nghiệp' AS mo_ta,
    COUNT(*) AS so_luong_dong
FROM OLTP_QuanLyHocTap.dbo.lan_lam_bai

UNION ALL

SELECT
    N'DW' AS phan_he,
    N'DW_QuanLyHocTap.dbo.fact_ket_qua_thi' AS ten_bang,
    N'Fact bài thi (Đã lọc qua Quality Gate 7 luật)' AS mo_ta,
    COUNT(*) AS so_luong_dong
FROM DW_QuanLyHocTap.dbo.fact_ket_qua_thi

UNION ALL

SELECT
    N'OLTP' AS phan_he,
    N'OLTP_QuanLyHocTap.dbo.phien_hoc' AS ten_bang,
    N'Dữ liệu phiên học LMS gốc từ ứng dụng tác nghiệp' AS mo_ta,
    COUNT(*) AS so_luong_dong
FROM OLTP_QuanLyHocTap.dbo.phien_hoc

UNION ALL

SELECT
    N'DW' AS phan_he,
    N'DW_QuanLyHocTap.dbo.fact_chuyen_can' AS ten_bang,
    N'Fact chuyên cần (Đã lọc qua Quality Gate 7 luật)' AS mo_ta,
    COUNT(*) AS so_luong_dong
FROM DW_QuanLyHocTap.dbo.fact_chuyen_can

UNION ALL

SELECT
    N'OLTP' AS phan_he,
    N'OLTP_QuanLyHocTap.dbo.hoc_sinh' AS ten_bang,
    N'Danh mục sinh viên hiện thời' AS mo_ta,
    COUNT(*) AS so_luong_dong
FROM OLTP_QuanLyHocTap.dbo.hoc_sinh

UNION ALL

SELECT
    N'DW' AS phan_he,
    N'DW_QuanLyHocTap.dbo.dim_hoc_sinh (Học sinh thực tế)' AS ten_bang,
    N'Chiều sinh viên SCD2 (Đã gồm lịch sử phiên bản, trừ dummy -1)' AS mo_ta,
    COUNT(*) AS so_luong_dong
FROM DW_QuanLyHocTap.dbo.dim_hoc_sinh
WHERE hoc_sinh_key > 0;
GO

-- 2. ĐỐI SOÁT CHI TIẾT TỶ LỆ DỮ LIỆU ĐƯỢC CHẤP NHẬN VÀO KHO DỮ LIỆU
SELECT
    N'Bài thi trắc nghiệm (Exam)' AS luong_du_lieu,
    (SELECT COUNT(*) FROM OLTP_QuanLyHocTap.dbo.lan_lam_bai) AS tong_oltp,
    (SELECT COUNT(*) FROM DW_QuanLyHocTap.dbo.fact_ket_qua_thi) AS tong_dw,
    (SELECT COUNT(*) FROM OLTP_QuanLyHocTap.dbo.lan_lam_bai) - (SELECT COUNT(*) FROM DW_QuanLyHocTap.dbo.fact_ket_qua_thi) AS so_luong_bi_loai,
    CAST((SELECT COUNT(*) FROM DW_QuanLyHocTap.dbo.fact_ket_qua_thi) * 100.0 / (SELECT COUNT(*) FROM OLTP_QuanLyHocTap.dbo.lan_lam_bai) AS DECIMAL(5,2)) AS ty_le_hop_le_phan_tram

UNION ALL

SELECT
    N'Phiên học LMS (Session)' AS luong_du_lieu,
    (SELECT COUNT(*) FROM OLTP_QuanLyHocTap.dbo.phien_hoc) AS tong_oltp,
    (SELECT COUNT(*) FROM DW_QuanLyHocTap.dbo.fact_chuyen_can) AS tong_dw,
    (SELECT COUNT(*) FROM OLTP_QuanLyHocTap.dbo.phien_hoc) - (SELECT COUNT(*) FROM DW_QuanLyHocTap.dbo.fact_chuyen_can) AS so_luong_bi_loai,
    CAST((SELECT COUNT(*) FROM DW_QuanLyHocTap.dbo.fact_chuyen_can) * 100.0 / (SELECT COUNT(*) FROM OLTP_QuanLyHocTap.dbo.phien_hoc) AS DECIMAL(5,2)) AS ty_le_hop_le_phan_tram;
GO
