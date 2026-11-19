/* ============================================================================
   BỘ TRUY VẤN MINH HỌA TRÊN SSMS - BTL KHO DỮ LIỆU (NHÓM 9)
   Server: localhost (Windows Authentication) | Database mặc định: DW_QuanLyHocTap
   Hướng dẫn: Bôi đen từng cụm hoặc từng lệnh rồi bấm F5 để chạy minh họa.
   ============================================================================ */
USE DW_QuanLyHocTap;


GO
/* ----------------------------------------------------------------------------
   CỤM 1: ĐỐI SOÁT MẺ ETL, WATERMARK VÀ CỔNG CHẤT LƯỢNG 7 LUẬT
   (Dùng để chứng minh: Nguồn = Nạp + Loại và dữ liệu lỗi được đẩy về etl_reject)
   ---------------------------------------------------------------------------- */
-- 1A. Lịch sử các mẻ chạy ETL và đối soát số dòng
SELECT   TOP 10 batch_id,
                trigger_name,
                started_at,
                duration_ms,
                src_exam,
                loaded_exam,
                rejected_exam,
                unknown_exam,
                src_session,
                loaded_session,
                rejected_session,
                unknown_session,
                src_event,
                scd_new,
                status
FROM     dbo.etl_batch
ORDER BY batch_id DESC;

-- 1B. Các dòng dữ liệu bị Cổng chất lượng 7 luật từ chối
SELECT   TOP 20 id,
                batch_id,
                nguon,
                nguon_id,
                ly_do,
                created_at,
                du_lieu
FROM     dbo.etl_reject
ORDER BY id DESC;

-- 1C. Ba mốc Watermark tăng trưởng từ OLTP
SELECT   stream,
         last_id
FROM     dbo.etl_watermark
ORDER BY stream;


GO
/* ----------------------------------------------------------------------------
   CỤM 2: KIỂM CHỨNG SCD TYPE 2 CHO SINH VIÊN B23DCKD004
   (Chứng minh: v1 lớp D23CQKD03 is_current=0 và v2 lớp D23CQCN01 is_current=1;
    Fact gắn đúng phiên bản tại thời điểm nộp bài, không ghi đè quá khứ)
   ---------------------------------------------------------------------------- */
-- 2A. Hai phiên bản lịch sử trong dim_hoc_sinh
SELECT   HocSinhKey,
         MaHocSinh,
         HoTen,
         Lop,
         TrangThaiHocVu,
         LyDo,
         Start_Date,
         End_Date,
         Is_Current,
         VersionNo
FROM     dbo.vw_dim_hoc_sinh_scd
WHERE    MaHocSinh = N'B23DCKD004'
ORDER BY VersionNo;

-- 2B. Kiểm tra từng bài thi của B23DCKD004 trỏ đúng khóa phiên bản theo thời gian
SELECT   t.ngay AS ngay_thi,
         m.ma_mon,
         f.diem_so,
         h.hoc_sinh_key,
         h.version_no,
         h.lop AS lop_tai_thoi_diem_thi,
         h.start_date,
         h.end_date
FROM     dbo.fact_ket_qua_thi AS f
         INNER JOIN
         dbo.dim_hoc_sinh AS h
         ON h.hoc_sinh_key = f.hoc_sinh_key
         INNER JOIN
         dbo.dim_thoi_gian AS t
         ON t.date_key = f.date_key
         INNER JOIN
         dbo.dim_mon_hoc AS m
         ON m.mon_hoc_key = f.mon_hoc_key
WHERE    h.ma_hoc_sinh = N'B23DCKD004'
ORDER BY t.ngay;


GO
/* ----------------------------------------------------------------------------
   CỤM 3: DRILL-ACROSS HAI NGHIỆP VỤ CHỐNG FAN-OUT (B23DCKD004 - MÔN CSDL)
   (So sánh: View chuẩn trả 5 bài thi / 26 điểm & 7 phiên học / 110.5 phút;
    JOIN thẳng 2 Fact bị nhân chéo thành 35 dòng / 182 điểm / 552.8 phút)
   ---------------------------------------------------------------------------- */
-- 3A. Cách ĐÚNG: Đọc qua dbo.vw_drill_across (GROUP BY từng Fact trước khi FULL OUTER JOIN)
SELECT ma_hoc_sinh,
       ho_ten,
       lop_hien_tai,
       ma_mon,
       ten_mon,
       so_luot_thi,
       CAST (so_luot_thi * diem_tb AS DECIMAL (10, 2)) AS tong_diem,
       diem_tb,
       so_phien,
       tong_phut,
       diem_cc
FROM   dbo.vw_drill_across
WHERE  ma_hoc_sinh = N'B23DCKD004'
       AND ma_mon = N'CSDL';

-- 3B. Cách SAI (chứng minh bẫy Fan-out khi JOIN thẳng 2 bảng Fact)
SELECT COUNT(*) AS so_dong_bi_nhan,
       SUM(f1.diem_so) AS tong_diem_bi_nhan,
       SUM(f2.thoi_luong_phut) AS tong_phut_bi_nhan
FROM   dbo.fact_ket_qua_thi AS f1
       INNER JOIN
       dbo.fact_chuyen_can AS f2
       ON f1.hoc_sinh_key = f2.hoc_sinh_key
          AND f1.mon_hoc_key = f2.mon_hoc_key
       INNER JOIN
       dbo.dim_hoc_sinh AS h
       ON h.hoc_sinh_key = f1.hoc_sinh_key
       INNER JOIN
       dbo.dim_mon_hoc AS m
       ON m.mon_hoc_key = f1.mon_hoc_key
WHERE  h.ma_hoc_sinh = N'B23DCKD004'
       AND m.ma_mon = N'CSDL';

-- 3C. Tổng quan các cặp có cả 2 bên hoặc chỉ có 1 bên trên vw_drill_across
SELECT COUNT(*) AS tong_cap_sv_mon,
       SUM(CASE WHEN so_luot_thi IS NOT NULL
                     AND so_phien IS NOT NULL THEN 1 ELSE 0 END) AS co_ca_hai,
       SUM(CASE WHEN so_luot_thi IS NOT NULL
                     AND so_phien IS NULL THEN 1 ELSE 0 END) AS chi_co_diem,
       SUM(CASE WHEN so_luot_thi IS NULL
                     AND so_phien IS NOT NULL THEN 1 ELSE 0 END) AS chi_co_chuyen_can
FROM   dbo.vw_drill_across;


GO
/* ----------------------------------------------------------------------------
   CỤM 4: TỐI ƯU TRUY VẤN BẰNG INDEXED VIEW (MATERIALIZED VIEW)
   Lưu ý: Bấm Ctrl + M (Include Actual Execution Plan) trước khi bấm F5,
   sau đó xem tab "Execution Plan" và tab "Messages" (Logical Reads) để chụp ảnh.
   ---------------------------------------------------------------------------- */
SET STATISTICS IO, TIME ON;

-- 4A. Truy vấn gốc: Quét toàn bộ 344 dòng fact_ket_qua_thi rồi JOIN + GROUP BY
SELECT   t.nam,
         t.thang,
         m.ten_mon,
         h.lop,
         f.loai_bai,
         COUNT_BIG(*) AS so_luot,
         SUM(f.diem_so) AS tong_diem
FROM     dbo.fact_ket_qua_thi AS f
         INNER JOIN
         dbo.dim_thoi_gian AS t
         ON t.date_key = f.date_key
         INNER JOIN
         dbo.dim_mon_hoc AS m
         ON m.mon_hoc_key = f.mon_hoc_key
         INNER JOIN
         dbo.dim_hoc_sinh AS h
         ON h.hoc_sinh_key = f.hoc_sinh_key
WHERE    f.date_key > 0
GROUP BY t.nam, t.thang, m.ten_mon, h.lop, f.loai_bai
ORDER BY t.nam, t.thang, m.ten_mon, h.lop;

-- 4B. Truy vấn tối ưu: Đọc thẳng từ Indexed View (chỉ 109 dòng đã tổng hợp sẵn)
SELECT   nam,
         thang,
         ten_mon,
         lop,
         loai_bai,
         so_luot,
         tong_diem
FROM     dbo.iv_diem_theo_mon_thang WITH (NOEXPAND)
ORDER BY nam, thang, ten_mon, lop;

SET STATISTICS IO, TIME OFF;


GO
/* ----------------------------------------------------------------------------
   CỤM 5: KIỂM TRA TÁCH BIỆT OLTP - DW TRƯỚC VÀ SAU KHI CHẠY DAGSTER
   (Chạy để thấy sự chênh lệch trước khi Materialize trên http://127.0.0.1:3000)
   ---------------------------------------------------------------------------- */
SELECT N'OLTP_QuanLyHocTap.lan_lam_bai' AS nguon,
       COUNT(*) AS so_dong
FROM   OLTP_QuanLyHocTap.dbo.lan_lam_bai
UNION ALL
SELECT N'DW_QuanLyHocTap.fact_ket_qua_thi',
       COUNT(*)
FROM   DW_QuanLyHocTap.dbo.fact_ket_qua_thi
UNION ALL
SELECT N'OLTP_QuanLyHocTap.phien_hoc',
       COUNT(*)
FROM   OLTP_QuanLyHocTap.dbo.phien_hoc
UNION ALL
SELECT N'DW_QuanLyHocTap.fact_chuyen_can',
       COUNT(*)
FROM   DW_QuanLyHocTap.dbo.fact_chuyen_can
UNION ALL
SELECT N'DW_QuanLyHocTap.dim_hoc_sinh (SCD)',
       COUNT(*)
FROM   DW_QuanLyHocTap.dbo.dim_hoc_sinh
WHERE  hoc_sinh_key > 0;