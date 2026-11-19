USE DW_QuanLyHocTap;
GO

-- ==========================================================================================
-- BÀI TẬP LỚN KHO DỮ LIỆU - DEMO 01: ĐỐI SOÁT ETL & QUALITY GATE (CỔNG CHẤT LƯỢNG DỮ LIỆU)
-- Hướng dẫn: Mở file trên SSMS và nhấn F5 để thực thi toàn bộ script.
-- ==========================================================================================

-- 1. TRUY VẤN TOP 10 LẦN CHẠY ETL BATCH MỚI NHẤT
-- Mục đích: Chứng minh bất biến bảo toàn dữ liệu: Nguồn = Nạp + Loại (Source = Loaded + Rejected).
SELECT TOP 10
    batch_id,
    trigger_name,
    started_at,
    finished_at,
    duration_ms,
    status,
    -- Luồng bài thi (Exam Stream)
    src_exam,
    loaded_exam,
    rejected_exam,
    unknown_exam,
    (loaded_exam + rejected_exam) AS kiem_tra_tong_exam,
    CASE 
        WHEN src_exam = (loaded_exam + rejected_exam) THEN N'HỢP LỆ (Bảo toàn)' 
        ELSE N'LỆCH' 
    END AS bat_bien_exam,
    -- Luồng phiên học LMS (Session Stream)
    src_session,
    loaded_session,
    rejected_session,
    unknown_session,
    (loaded_session + rejected_session) AS kiem_tra_tong_session,
    CASE 
        WHEN src_session = (loaded_session + rejected_session) THEN N'HỢP LỆ (Bảo toàn)' 
        ELSE N'LỆCH' 
    END AS bat_bien_session,
    -- Luồng sự kiện học vụ SCD2
    src_event,
    scd_new
FROM dbo.etl_batch
ORDER BY batch_id DESC;
GO

-- 2. TRUY VẤN TOP 20 BẢN GHI BỊ TỪ CHỐI BỞI CỔNG CHẤT LƯỢNG 7 LUẬT (ETL REJECT)
-- Mục đích: Kiểm tra các dòng dữ liệu bẩn / dị thường bị chặn lại tại Quality Gate.
SELECT TOP 20
    id AS reject_id,
    batch_id,
    nguon,
    nguon_id,
    ly_do,
    du_lieu,
    created_at
FROM dbo.etl_reject
ORDER BY id DESC;
GO

-- 3. TRUY VẤN MỐC TĂNG TRƯỞNG HIGH-WATERMARK (ETL WATERMARK)
-- Mục đích: Theo dõi ID tác nghiệp lớn nhất đã nạp thành công vào Kho dữ liệu của 3 luồng.
SELECT
    stream AS luong_du_lieu,
    last_id AS id_tac_nghiep_lon_nhat_da_nap,
    CASE stream
        WHEN N'lan_lam_bai' THEN N'Mốc ID lần làm bài thi trắc nghiệm (OLTP)'
        WHEN N'phien_hoc' THEN N'Mốc ID phiên học LMS trực tuyến (OLTP)'
        WHEN N'su_kien_hoc_vu' THEN N'Mốc ID sự kiện biến động học vụ SCD2 (OLTP)'
        ELSE N'Khác'
    END AS mo_ta
FROM dbo.etl_watermark
ORDER BY stream;
GO
