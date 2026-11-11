/*
    Kho học tập trên SQL Server.
    Chạy toàn bộ file này trong SSMS trước sql/07_sqlserver_seed_data.sql.
    Script tạo lại hai database. Dữ liệu cũ trong hai database này sẽ bị xóa.
    Collation Vietnamese_CI_AS để thứ tự tiếng Việt đúng khi xếp lớp và môn.
*/

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET ARITHABORT ON;
SET NUMERIC_ROUNDABORT OFF;
GO

IF DB_ID(N'OLTP_QuanLyHocTap') IS NOT NULL
BEGIN
    ALTER DATABASE OLTP_QuanLyHocTap SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE OLTP_QuanLyHocTap;
END
GO

-- Use the instance data directory so this script runs on any machine.
CREATE DATABASE OLTP_QuanLyHocTap COLLATE Vietnamese_CI_AS;
GO

USE OLTP_QuanLyHocTap;
GO

/* ma_hs cố ý không có khóa ngoại: nguồn được phép phát sinh mã lạ. */
CREATE TABLE dbo.hoc_sinh (
    ma_hs NVARCHAR(30) NOT NULL PRIMARY KEY,
    ho_ten NVARCHAR(120) NOT NULL,
    ngay_sinh DATE NULL,
    email NVARCHAR(120) NULL,
    lop NVARCHAR(20) NOT NULL,
    trang_thai_hoc_vu NVARCHAR(40) NOT NULL,
    ngay_vao_hoc DATETIME2(0) NOT NULL
);

CREATE TABLE dbo.mon_hoc (
    ma_mon NVARCHAR(20) NOT NULL PRIMARY KEY,
    ten_mon NVARCHAR(120) NOT NULL,
    so_tin_chi INT NOT NULL,
    khoa NVARCHAR(80) NOT NULL
);

CREATE TABLE dbo.de_thi (
    ma_de NVARCHAR(20) NOT NULL PRIMARY KEY,
    ma_mon NVARCHAR(20) NOT NULL REFERENCES dbo.mon_hoc(ma_mon),
    ten_de NVARCHAR(200) NOT NULL,
    loai NVARCHAR(20) NOT NULL,
    do_kho NVARCHAR(20) NOT NULL,
    so_cau INT NOT NULL,
    thoi_gian_phut INT NOT NULL
);

CREATE TABLE dbo.cau_hoi (
    ma_cau INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ma_de NVARCHAR(20) NOT NULL REFERENCES dbo.de_thi(ma_de),
    noi_dung NVARCHAR(500) NOT NULL,
    phuong_an_a NVARCHAR(300) NOT NULL,
    phuong_an_b NVARCHAR(300) NOT NULL,
    phuong_an_c NVARCHAR(300) NOT NULL,
    phuong_an_d NVARCHAR(300) NOT NULL,
    dap_an_dung NVARCHAR(1) NOT NULL
);

CREATE TABLE dbo.bai_hoc (
    ma_bai NVARCHAR(20) NOT NULL PRIMARY KEY,
    ma_mon NVARCHAR(20) NOT NULL REFERENCES dbo.mon_hoc(ma_mon),
    ten_bai NVARCHAR(200) NOT NULL,
    loai_noi_dung NVARCHAR(20) NOT NULL,
    thoi_luong_phut INT NOT NULL
);

CREATE TABLE dbo.lan_lam_bai (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ma_hs NVARCHAR(30) NOT NULL,
    ma_de NVARCHAR(20) NOT NULL,
    nop_luc DATETIME2(0) NOT NULL,
    so_cau_dung INT NOT NULL,
    so_cau_sai INT NOT NULL,
    tong_so_cau INT NOT NULL,
    diem DECIMAL(6,2) NOT NULL,
    ty_le_dung DECIMAL(8,4) NOT NULL,
    thoi_gian_giay INT NOT NULL,
    trang_thai NVARCHAR(20) NOT NULL CONSTRAINT df_bai_trang_thai DEFAULT N'DA_NOP'
);

CREATE TABLE dbo.phien_hoc (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ma_hs NVARCHAR(30) NOT NULL,
    ma_bai NVARCHAR(20) NOT NULL,
    ket_thuc_luc DATETIME2(0) NOT NULL,
    thoi_luong_giay INT NOT NULL,
    so_video INT NOT NULL,
    so_tuong_tac INT NOT NULL,
    diem_chuyen_can DECIMAL(6,2) NOT NULL,
    trang_thai NVARCHAR(20) NOT NULL CONSTRAINT df_phien_trang_thai DEFAULT N'HOAN_THANH'
);

CREATE TABLE dbo.su_kien_hoc_vu (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ma_hs NVARCHAR(30) NOT NULL,
    thoi_diem DATETIME2(0) NOT NULL,
    lop_moi NVARCHAR(20) NOT NULL,
    trang_thai_moi NVARCHAR(40) NOT NULL,
    ly_do NVARCHAR(40) NOT NULL
);

CREATE NONCLUSTERED INDEX ix_oltp_bai_hs ON dbo.lan_lam_bai(ma_hs);
CREATE NONCLUSTERED INDEX ix_oltp_phien_hs ON dbo.phien_hoc(ma_hs);
CREATE NONCLUSTERED INDEX ix_oltp_sk_hs ON dbo.su_kien_hoc_vu(ma_hs);
GO

IF DB_ID(N'DW_QuanLyHocTap') IS NOT NULL
BEGIN
    ALTER DATABASE DW_QuanLyHocTap SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE DW_QuanLyHocTap;
END
GO

-- Use the instance data directory so this script runs on any machine.
CREATE DATABASE DW_QuanLyHocTap COLLATE Vietnamese_CI_AS;
GO

USE DW_QuanLyHocTap;
GO

CREATE TABLE dbo.dim_thoi_gian (
    date_key INT NOT NULL PRIMARY KEY,
    ngay DATE NULL,
    thu NVARCHAR(20) NULL,
    tuan INT NOT NULL,
    thang INT NOT NULL,
    ten_thang NVARCHAR(20) NOT NULL,
    quy INT NOT NULL,
    nam INT NOT NULL,
    hoc_ky NVARCHAR(10) NOT NULL,
    nam_hoc NVARCHAR(12) NOT NULL
);

/* SCD Type 2: start_date, end_date, is_current. Khóa -1 là unknown member. */
CREATE TABLE dbo.dim_hoc_sinh (
    hoc_sinh_key INT NOT NULL PRIMARY KEY,
    ma_hoc_sinh NVARCHAR(30) NOT NULL,
    ho_ten NVARCHAR(120) NOT NULL,
    ngay_sinh DATE NULL,
    lop NVARCHAR(20) NOT NULL,
    trang_thai_hoc_vu NVARCHAR(40) NOT NULL,
    ly_do NVARCHAR(40) NOT NULL,
    start_date DATETIME2(0) NOT NULL,
    end_date DATETIME2(0) NOT NULL,
    is_current TINYINT NOT NULL,
    version_no INT NOT NULL,
    CONSTRAINT ck_hs_current CHECK (is_current IN (0, 1))
);

CREATE TABLE dbo.dim_mon_hoc (
    mon_hoc_key INT NOT NULL PRIMARY KEY,
    ma_mon NVARCHAR(20) NOT NULL UNIQUE,
    ten_mon NVARCHAR(120) NOT NULL,
    so_tin_chi INT NOT NULL,
    khoa NVARCHAR(80) NOT NULL
);

CREATE TABLE dbo.dim_de_thi (
    de_thi_key INT NOT NULL PRIMARY KEY,
    ma_de NVARCHAR(20) NOT NULL UNIQUE,
    ten_de NVARCHAR(200) NOT NULL,
    loai NVARCHAR(20) NOT NULL,
    do_kho NVARCHAR(20) NOT NULL,
    so_cau INT NOT NULL,
    ma_mon NVARCHAR(20) NOT NULL
);

CREATE TABLE dbo.dim_bai_hoc (
    bai_hoc_key INT NOT NULL PRIMARY KEY,
    ma_bai NVARCHAR(20) NOT NULL UNIQUE,
    ten_bai NVARCHAR(200) NOT NULL,
    loai_noi_dung NVARCHAR(20) NOT NULL,
    thoi_luong_phut INT NOT NULL,
    ma_mon NVARCHAR(20) NOT NULL
);

CREATE TABLE dbo.fact_ket_qua_thi (
    fact_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    lan_lam_id INT NOT NULL UNIQUE,
    hoc_sinh_key INT NOT NULL REFERENCES dbo.dim_hoc_sinh(hoc_sinh_key),
    date_key INT NOT NULL REFERENCES dbo.dim_thoi_gian(date_key),
    mon_hoc_key INT NOT NULL REFERENCES dbo.dim_mon_hoc(mon_hoc_key),
    de_thi_key INT NOT NULL REFERENCES dbo.dim_de_thi(de_thi_key),
    diem_so DECIMAL(6,2) NOT NULL,
    so_cau_dung INT NOT NULL,
    so_cau_sai INT NOT NULL,
    tong_so_cau INT NOT NULL,
    ty_le_dung DECIMAL(8,4) NOT NULL,
    thoi_gian_lam_giay INT NOT NULL,
    loai_bai NVARCHAR(20) NOT NULL,
    CONSTRAINT ck_diem CHECK (diem_so >= 0 AND diem_so <= 10),
    CONSTRAINT ck_cau CHECK (so_cau_dung >= 0 AND so_cau_sai >= 0 AND tong_so_cau > 0),
    CONSTRAINT ck_tong_cau CHECK (so_cau_dung + so_cau_sai = tong_so_cau),
    CONSTRAINT ck_ty_le CHECK (ty_le_dung >= 0 AND ty_le_dung <= 1),
    CONSTRAINT ck_giay CHECK (thoi_gian_lam_giay > 0 AND thoi_gian_lam_giay <= 14400)
);

CREATE TABLE dbo.fact_chuyen_can (
    fact_id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    phien_hoc_id INT NOT NULL UNIQUE,
    hoc_sinh_key INT NOT NULL REFERENCES dbo.dim_hoc_sinh(hoc_sinh_key),
    date_key INT NOT NULL REFERENCES dbo.dim_thoi_gian(date_key),
    mon_hoc_key INT NOT NULL REFERENCES dbo.dim_mon_hoc(mon_hoc_key),
    bai_hoc_key INT NOT NULL REFERENCES dbo.dim_bai_hoc(bai_hoc_key),
    thoi_luong_phut DECIMAL(10,2) NOT NULL,
    so_video_da_xem INT NOT NULL,
    so_tuong_tac INT NOT NULL,
    diem_chuyen_can DECIMAL(6,2) NOT NULL,
    loai_noi_dung NVARCHAR(20) NOT NULL,
    CONSTRAINT ck_phut CHECK (thoi_luong_phut >= 0),
    CONSTRAINT ck_video CHECK (so_video_da_xem IN (0, 1)),
    CONSTRAINT ck_tuong_tac CHECK (so_tuong_tac >= 0),
    CONSTRAINT ck_diem_cc CHECK (diem_chuyen_can >= 0 AND diem_chuyen_can <= 10)
);

CREATE NONCLUSTERED INDEX ix_fact_exam_hs ON dbo.fact_ket_qua_thi(hoc_sinh_key);
CREATE NONCLUSTERED INDEX ix_fact_exam_ngay ON dbo.fact_ket_qua_thi(date_key);
CREATE NONCLUSTERED INDEX ix_fact_exam_mon ON dbo.fact_ket_qua_thi(mon_hoc_key);
CREATE NONCLUSTERED INDEX ix_fact_exam_de ON dbo.fact_ket_qua_thi(de_thi_key);
CREATE NONCLUSTERED INDEX ix_fact_exam_loai ON dbo.fact_ket_qua_thi(loai_bai);

CREATE NONCLUSTERED INDEX ix_fact_cc_hs ON dbo.fact_chuyen_can(hoc_sinh_key);
CREATE NONCLUSTERED INDEX ix_fact_cc_ngay ON dbo.fact_chuyen_can(date_key);
CREATE NONCLUSTERED INDEX ix_fact_cc_mon ON dbo.fact_chuyen_can(mon_hoc_key);
CREATE NONCLUSTERED INDEX ix_fact_cc_bai ON dbo.fact_chuyen_can(bai_hoc_key);
CREATE NONCLUSTERED INDEX ix_fact_cc_loai ON dbo.fact_chuyen_can(loai_noi_dung);

CREATE NONCLUSTERED INDEX ix_dim_hs_hien_tai ON dbo.dim_hoc_sinh(ma_hoc_sinh, is_current);
CREATE NONCLUSTERED INDEX ix_dim_hs_pit ON dbo.dim_hoc_sinh(ma_hoc_sinh, start_date, end_date);
CREATE UNIQUE NONCLUSTERED INDEX ux_dim_hs_ver ON dbo.dim_hoc_sinh(ma_hoc_sinh, version_no);
GO

CREATE VIEW dbo.vw_dim_hoc_sinh_scd
AS
SELECT
    hoc_sinh_key AS HocSinhKey,
    ma_hoc_sinh AS MaHocSinh,
    ho_ten AS HoTen,
    lop AS Lop,
    trang_thai_hoc_vu AS TrangThaiHocVu,
    ly_do AS LyDo,
    start_date AS Start_Date,
    end_date AS End_Date,
    is_current AS Is_Current,
    version_no AS VersionNo
FROM dbo.dim_hoc_sinh;
GO

/* Unknown member khóa -1, có mặt trước khi nạp fact. */
INSERT INTO dbo.dim_thoi_gian (date_key, ngay, thu, tuan, thang, ten_thang, quy, nam, hoc_ky, nam_hoc)
VALUES (-1, NULL, N'N/A', 0, 0, N'N/A', 0, 0, N'N/A', N'N/A');

INSERT INTO dbo.dim_hoc_sinh (
    hoc_sinh_key, ma_hoc_sinh, ho_ten, ngay_sinh, lop, trang_thai_hoc_vu,
    ly_do, start_date, end_date, is_current, version_no
) VALUES (
    -1, N'UNKNOWN', N'Không xác định', NULL, N'N/A', N'KHONG_XAC_DINH',
    N'UNKNOWN', '1900-01-01', '9999-12-31 23:59:59', 1, 0
);

INSERT INTO dbo.dim_mon_hoc (mon_hoc_key, ma_mon, ten_mon, so_tin_chi, khoa)
VALUES (-1, N'UNKNOWN', N'Không xác định', 0, N'N/A');

INSERT INTO dbo.dim_de_thi (de_thi_key, ma_de, ten_de, loai, do_kho, so_cau, ma_mon)
VALUES (-1, N'UNKNOWN', N'Không xác định', N'KHONG_XAC_DINH', N'N/A', 0, N'UNKNOWN');

INSERT INTO dbo.dim_bai_hoc (bai_hoc_key, ma_bai, ten_bai, loai_noi_dung, thoi_luong_phut, ma_mon)
VALUES (-1, N'UNKNOWN', N'Không xác định', N'KHONG_XAC_DINH', 0, N'UNKNOWN');
GO

/*
    Indexed view là materialized view của SQL Server.
    FULL OUTER JOIN không được phép trong indexed view, nên drill-across để ở view thường bên dưới.
    Số đo trung bình tính từ SUM và COUNT_BIG, không dùng AVG trong view được đánh chỉ mục.
*/
CREATE VIEW dbo.iv_diem_theo_mon_thang
WITH SCHEMABINDING
AS
SELECT
    t.nam,
    t.thang,
    t.hoc_ky,
    t.nam_hoc,
    f.mon_hoc_key,
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
GROUP BY t.nam, t.thang, t.hoc_ky, t.nam_hoc, f.mon_hoc_key, m.ten_mon, h.lop, f.loai_bai;
GO

CREATE UNIQUE CLUSTERED INDEX ux_iv_diem_theo_mon_thang
ON dbo.iv_diem_theo_mon_thang (nam, thang, mon_hoc_key, lop, loai_bai);
GO

CREATE VIEW dbo.iv_chuyen_can_theo_lop_tuan
WITH SCHEMABINDING
AS
SELECT
    t.nam,
    t.tuan,
    t.hoc_ky,
    t.nam_hoc,
    f.mon_hoc_key,
    m.ten_mon,
    h.lop,
    f.loai_noi_dung,
    COUNT_BIG(*) AS so_phien,
    SUM(f.thoi_luong_phut) AS tong_phut,
    SUM(f.so_video_da_xem) AS tong_video,
    SUM(f.so_tuong_tac) AS tong_tuong_tac,
    SUM(f.diem_chuyen_can) AS tong_diem_cc
FROM dbo.fact_chuyen_can AS f
INNER JOIN dbo.dim_thoi_gian AS t ON t.date_key = f.date_key
INNER JOIN dbo.dim_mon_hoc AS m ON m.mon_hoc_key = f.mon_hoc_key
INNER JOIN dbo.dim_hoc_sinh AS h ON h.hoc_sinh_key = f.hoc_sinh_key
WHERE f.date_key > 0
GROUP BY t.nam, t.tuan, t.hoc_ky, t.nam_hoc, f.mon_hoc_key, m.ten_mon, h.lop, f.loai_noi_dung;
GO

CREATE UNIQUE CLUSTERED INDEX ux_iv_chuyen_can_theo_lop_tuan
ON dbo.iv_chuyen_can_theo_lop_tuan (nam, tuan, mon_hoc_key, lop, loai_noi_dung);
GO

CREATE VIEW dbo.vw_diem_theo_mon_thang
AS
SELECT
    nam, thang, hoc_ky, nam_hoc, mon_hoc_key, ten_mon, lop, loai_bai,
    so_luot, tong_diem,
    CAST(tong_diem AS DECIMAL(18,4)) / so_luot AS diem_tb,
    tong_cau_dung, tong_cau,
    CAST(tong_cau_dung AS DECIMAL(18,4)) / NULLIF(tong_cau, 0) AS ty_le_dung,
    tong_giay
FROM dbo.iv_diem_theo_mon_thang;
GO

/* Drill-across: gộp từng fact về hạt mã học sinh x môn, rồi FULL OUTER JOIN. */
CREATE VIEW dbo.vw_drill_across
AS
WITH diem AS (
    SELECT
        h.ma_hoc_sinh,
        m.ma_mon,
        m.ten_mon,
        COUNT_BIG(*) AS so_luot_thi,
        SUM(f.diem_so) AS tong_diem,
        SUM(f.so_cau_dung) AS so_cau_dung
    FROM dbo.fact_ket_qua_thi AS f
    INNER JOIN dbo.dim_hoc_sinh AS h ON h.hoc_sinh_key = f.hoc_sinh_key
    INNER JOIN dbo.dim_mon_hoc AS m ON m.mon_hoc_key = f.mon_hoc_key
    WHERE f.date_key > 0 AND f.hoc_sinh_key > 0
    GROUP BY h.ma_hoc_sinh, m.ma_mon, m.ten_mon
),
chuyen AS (
    SELECT
        h.ma_hoc_sinh,
        m.ma_mon,
        m.ten_mon,
        COUNT_BIG(*) AS so_phien,
        SUM(f.thoi_luong_phut) AS tong_phut,
        SUM(f.so_video_da_xem) AS so_video,
        SUM(f.diem_chuyen_can) AS tong_diem_cc
    FROM dbo.fact_chuyen_can AS f
    INNER JOIN dbo.dim_hoc_sinh AS h ON h.hoc_sinh_key = f.hoc_sinh_key
    INNER JOIN dbo.dim_mon_hoc AS m ON m.mon_hoc_key = f.mon_hoc_key
    WHERE f.date_key > 0 AND f.hoc_sinh_key > 0
    GROUP BY h.ma_hoc_sinh, m.ma_mon, m.ten_mon
)
SELECT
    COALESCE(d.ma_hoc_sinh, c.ma_hoc_sinh) AS ma_hoc_sinh,
    cur.ho_ten,
    cur.lop AS lop_hien_tai,
    COALESCE(d.ma_mon, c.ma_mon) AS ma_mon,
    COALESCE(d.ten_mon, c.ten_mon) AS ten_mon,
    d.so_luot_thi,
    CAST(d.tong_diem AS DECIMAL(18,4)) / NULLIF(d.so_luot_thi, 0) AS diem_tb,
    c.so_phien,
    c.tong_phut,
    CAST(c.tong_diem_cc AS DECIMAL(18,4)) / NULLIF(c.so_phien, 0) AS diem_cc
FROM diem AS d
FULL OUTER JOIN chuyen AS c
    ON d.ma_hoc_sinh = c.ma_hoc_sinh AND d.ma_mon = c.ma_mon
LEFT JOIN dbo.dim_hoc_sinh AS cur
    ON cur.ma_hoc_sinh = COALESCE(d.ma_hoc_sinh, c.ma_hoc_sinh) AND cur.is_current = 1;
GO

/* Đo sau khi đã chạy file nạp dữ liệu. Bỏ comment hai khối dưới trong SSMS. */
/*
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

SELECT nam, thang, ten_mon, lop, so_luot, tong_diem
FROM dbo.iv_diem_theo_mon_thang;

SELECT t.nam, t.thang, m.ten_mon, h.lop, COUNT_BIG(*) AS so_luot, SUM(f.diem_so) AS tong_diem
FROM dbo.fact_ket_qua_thi AS f
INNER JOIN dbo.dim_thoi_gian AS t ON t.date_key = f.date_key
INNER JOIN dbo.dim_mon_hoc AS m ON m.mon_hoc_key = f.mon_hoc_key
INNER JOIN dbo.dim_hoc_sinh AS h ON h.hoc_sinh_key = f.hoc_sinh_key
WHERE f.date_key > 0
GROUP BY t.nam, t.thang, m.ten_mon, h.lop;

SELECT ma_hoc_sinh, ten_mon, so_luot_thi, tong_phut
FROM dbo.vw_drill_across
WHERE ma_hoc_sinh = N'B23DCKD004' AND ma_mon = N'CSDL';

SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
*/
GO
