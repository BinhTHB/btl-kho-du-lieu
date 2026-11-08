/*
    CSDL tác nghiệp OLTP_QuanLyHocTap trên Microsoft SQL Server.
    Ứng dụng chạy từng lô (ngăn cách bằng GO). Tạo mới nếu chưa có, không xóa dữ liệu sẵn.
*/

IF COL_LENGTH(N'dbo.hoc_sinh', N'vai_tro') IS NULL
   AND OBJECT_ID(N'dbo.hoc_sinh', N'U') IS NOT NULL
    EXEC(N'ALTER TABLE dbo.hoc_sinh ADD vai_tro NVARCHAR(40) NULL');
GO

CREATE TABLE dbo.hoc_sinh (
    ma_hs NVARCHAR(30) NOT NULL PRIMARY KEY,
    ho_ten NVARCHAR(120) NOT NULL,
    ngay_sinh DATE NULL,
    email NVARCHAR(120) NULL,
    lop NVARCHAR(20) NOT NULL,
    trang_thai_hoc_vu NVARCHAR(40) NOT NULL,
    ngay_vao_hoc DATETIME2(0) NOT NULL,
    vai_tro NVARCHAR(40) NULL
);
GO

CREATE TABLE dbo.mon_hoc (
    ma_mon NVARCHAR(20) NOT NULL PRIMARY KEY,
    ten_mon NVARCHAR(120) NOT NULL,
    so_tin_chi INT NOT NULL,
    khoa NVARCHAR(80) NOT NULL
);
GO

CREATE TABLE dbo.de_thi (
    ma_de NVARCHAR(20) NOT NULL PRIMARY KEY,
    ma_mon NVARCHAR(20) NOT NULL REFERENCES dbo.mon_hoc(ma_mon),
    ten_de NVARCHAR(200) NOT NULL,
    loai NVARCHAR(20) NOT NULL,
    do_kho NVARCHAR(20) NOT NULL,
    so_cau INT NOT NULL,
    thoi_gian_phut INT NOT NULL
);
GO

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
GO

CREATE TABLE dbo.bai_hoc (
    ma_bai NVARCHAR(20) NOT NULL PRIMARY KEY,
    ma_mon NVARCHAR(20) NOT NULL REFERENCES dbo.mon_hoc(ma_mon),
    ten_bai NVARCHAR(200) NOT NULL,
    loai_noi_dung NVARCHAR(20) NOT NULL,
    thoi_luong_phut INT NOT NULL
);
GO

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
GO

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
GO

CREATE TABLE dbo.su_kien_hoc_vu (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ma_hs NVARCHAR(30) NOT NULL,
    thoi_diem DATETIME2(0) NOT NULL,
    lop_moi NVARCHAR(20) NOT NULL,
    trang_thai_moi NVARCHAR(40) NOT NULL,
    ly_do NVARCHAR(40) NOT NULL
);
GO

CREATE NONCLUSTERED INDEX ix_oltp_bai_hs ON dbo.lan_lam_bai(ma_hs);
GO
CREATE NONCLUSTERED INDEX ix_oltp_phien_hs ON dbo.phien_hoc(ma_hs);
GO
CREATE NONCLUSTERED INDEX ix_oltp_sk_hs ON dbo.su_kien_hoc_vu(ma_hs);
GO
