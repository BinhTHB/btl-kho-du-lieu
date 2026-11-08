import time

MUC = {
    "ngay": "t.ngay",
    "tuan": "CONCAT(CAST(t.nam AS varchar(4)), '-W', RIGHT(CONCAT('0', CAST(t.tuan AS varchar(2))), 2))",
    "thang": "CONCAT(CAST(t.nam AS varchar(4)), '-', RIGHT(CONCAT('0', CAST(t.thang AS varchar(2))), 2))",
    "hoc_ky": "CONCAT(t.nam_hoc, ' ', t.hoc_ky)",
    "nam": "t.nam_hoc",
}

NIVEAU = ["ngay", "tuan", "thang", "hoc_ky", "nam"]


def _packs(records, specs):
    return {
        "cot": [label for _key, label in specs],
        "dong": [[record[key] for key, _label in specs] for record in records],
    }


def _where(params, loai_col: str):
    clauses = ["f.date_key > 0", "h.hoc_sinh_key > 0"]
    args = []
    if params.get("ma_mon"):
        clauses.append("m.ma_mon = ?")
        args.append(params["ma_mon"])
    if params.get("lop"):
        clauses.append("h.lop = ?")
        args.append(params["lop"])
    if params.get("loai"):
        clauses.append(f"{loai_col} = ?")
        args.append(params["loai"])
    if params.get("tu_ngay"):
        clauses.append("t.ngay >= ?")
        args.append(params["tu_ngay"])
    if params.get("den_ngay"):
        clauses.append("t.ngay <= ?")
        args.append(params["den_ngay"])
    if params.get("hoc_ky"):
        clauses.append("t.hoc_ky = ?")
        args.append(params["hoc_ky"])
    if params.get("nam_hoc"):
        clauses.append("t.nam_hoc = ?")
        args.append(params["nam_hoc"])
    return " AND ".join(clauses), args


def _exam_sql(muc: str, where: str) -> str:
    bucket = MUC[muc]
    return f"""
        SELECT {bucket} AS moc,
               COUNT(*) AS so_luot,
               ROUND(AVG(f.diem_so), 2) AS diem_tb,
               SUM(f.so_cau_dung) AS so_cau_dung,
               SUM(f.tong_so_cau) AS tong_cau,
               ROUND(1.0 * SUM(f.so_cau_dung) / SUM(f.tong_so_cau), 4) AS ty_le_dung
        FROM fact_ket_qua_thi f
        JOIN dim_thoi_gian t ON t.date_key = f.date_key
        JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
        JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
        JOIN dim_de_thi d ON d.de_thi_key = f.de_thi_key
        WHERE {where}
        GROUP BY {bucket}
        ORDER BY 1
    """


def _cc_sql(muc: str, where: str) -> str:
    bucket = MUC[muc]
    return f"""
        SELECT {bucket} AS moc,
               COUNT(*) AS so_phien,
               ROUND(SUM(f.thoi_luong_phut), 1) AS tong_phut,
               SUM(f.so_video_da_xem) AS so_video,
               ROUND(AVG(f.diem_chuyen_can), 2) AS diem_cc
        FROM fact_chuyen_can f
        JOIN dim_thoi_gian t ON t.date_key = f.date_key
        JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
        JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
        WHERE {where}
        GROUP BY {bucket}
        ORDER BY 1
    """


def query_grouped(dw, params: dict) -> dict:
    muc = params.get("muc") or "thang"
    if muc not in MUC:
        raise ValueError("Mức thời gian không hợp lệ")
    source = params.get("nguon") or "ket_qua"
    if source == "ket_qua":
        where, args = _where(params, "f.loai_bai")
        sql = _exam_sql(muc, where)
        specs = [
            ("moc", "Mốc"),
            ("so_luot", "Số lượt"),
            ("diem_tb", "Điểm TB"),
            ("so_cau_dung", "Câu đúng"),
            ("tong_cau", "Tổng câu"),
            ("ty_le_dung", "Tỷ lệ đúng"),
        ]
    elif source == "chuyen_can":
        where, args = _where(params, "f.loai_noi_dung")
        sql = _cc_sql(muc, where)
        specs = [
            ("moc", "Mốc"),
            ("so_phien", "Số phiên"),
            ("tong_phut", "Tổng phút"),
            ("so_video", "Số video"),
            ("diem_cc", "Điểm CC"),
        ]
    else:
        raise ValueError("Nguồn fact không hợp lệ")
    found = [dict(row) for row in dw.execute(sql, args)]
    packed = _packs(found, specs)
    packed.update(
        {
            "kieu": "bang",
            "sql": " ".join(sql.split()),
            "tham_so": {**params, "muc": muc, "nguon": source},
            "so_dong": len(found),
        }
    )
    return packed


def query_pivot(dw, params: dict) -> dict:
    hang = params.get("hang") or "lop"
    cot = params.get("cot") or "mon"
    allowed = {"lop": "h.lop", "mon": "m.ten_mon", "loai": "f.loai_bai", "trang_thai": "h.trang_thai_hoc_vu"}
    if hang not in allowed or cot not in allowed or hang == cot:
        raise ValueError("Hàng và cột pivot phải là hai chiều khác nhau")
    where, args = _where(params, "f.loai_bai")
    sql = f"""
        SELECT {allowed[hang]} AS hang, {allowed[cot]} AS cot,
               ROUND(AVG(f.diem_so), 2) AS diem_tb, COUNT(*) AS so_luot
        FROM fact_ket_qua_thi f
        JOIN dim_thoi_gian t ON t.date_key = f.date_key
        JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
        JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
        WHERE {where}
        GROUP BY {allowed[hang]}, {allowed[cot]}
        ORDER BY 1, 2
    """
    found = [dict(row) for row in dw.execute(sql, args)]
    hang_labels, cot_labels = [], []
    for row in found:
        if row["hang"] not in hang_labels:
            hang_labels.append(row["hang"])
        if row["cot"] not in cot_labels:
            cot_labels.append(row["cot"])
    lookup = {(row["hang"], row["cot"]): row["diem_tb"] for row in found}
    matrix = [[lookup.get((h, c)) for c in cot_labels] for h in hang_labels]
    return {
        "kieu": "pivot",
        "thao_tac": params.get("thao_tac") or "Pivot",
        "hang_ten": hang,
        "cot_ten": cot,
        "hang": hang_labels,
        "cot": cot_labels,
        "matran": matrix,
        "sql": " ".join(sql.split()),
        "tham_so": params,
        "so_dong": len(found),
        "mo_ta": "Pivot xoay điểm trung bình: một chiều làm hàng, chiều kia làm cột. Ô trống là không có lượt thi.",
    }


def preset(dw, name: str) -> dict:
    if name == "roll-up":
        fine = query_grouped(dw, {"nguon": "ket_qua", "muc": "thang"})
        coarse = query_grouped(dw, {"nguon": "ket_qua", "muc": "hoc_ky", "thao_tac": "Roll-up"})
        coarse["thao_tac"] = "Roll-up"
        coarse["mo_ta"] = (
            f"Roll-up cuộn {fine['so_dong']} dòng mức tháng thành {coarse['so_dong']} dòng mức học kỳ. "
            "Số lượt cộng lại, điểm lấy trung bình, tỷ lệ đúng tính lại từ tổng câu."
        )
        return coarse
    if name == "drill-down":
        result = query_grouped(
            dw,
            {"nguon": "ket_qua", "muc": "thang", "hoc_ky": "HK1", "nam_hoc": "2026-2027", "thao_tac": "Drill-down"},
        )
        result["thao_tac"] = "Drill-down"
        result["mo_ta"] = (
            f"Drill-down từ học kỳ HK1 2026-2027 xuống {result['so_dong']} tháng. "
            "Bấm mức Ngày trên bộ lọc để khoan tiếp tới từng ngày."
        )
        return result
    if name == "slice":
        result = query_grouped(
            dw, {"nguon": "ket_qua", "muc": "thang", "ma_mon": "KDL", "thao_tac": "Slice"}
        )
        result["thao_tac"] = "Slice"
        result["mo_ta"] = (
            "Slice cắt một lát: chỉ giữ môn Kho dữ liệu, các chiều khác không bị khóa. "
            f"Kết quả còn {result['so_dong']} mốc tháng."
        )
        return result
    if name == "dice":
        result = query_grouped(
            dw,
            {
                "nguon": "ket_qua",
                "muc": "tuan",
                "ma_mon": "CSDL",
                "lop": "D23CQKD03",
                "tu_ngay": "2026-09-01",
                "den_ngay": "2026-11-04",
                "thao_tac": "Dice",
            },
        )
        result["thao_tac"] = "Dice"
        result["mo_ta"] = (
            "Dice cắt khối theo nhiều chiều cùng lúc: lớp D23CQKD03, môn Cơ sở dữ liệu, "
            f"từ 01/09/2026 đến 04/11/2026. Còn {result['so_dong']} tuần có bài nộp."
        )
        return result
    if name == "pivot":
        result = query_pivot(
            dw,
            {
                "hang": "lop",
                "cot": "mon",
                "hoc_ky": "HK1",
                "nam_hoc": "2026-2027",
                "thao_tac": "Pivot",
            },
        )
        result["mo_ta"] = (
            "Pivot đưa lớp xuống hàng và môn học sang cột. Ô là điểm trung bình học kỳ HK1 2026-2027. "
            "Đảo hàng với cột vẫn là cùng một khối dữ liệu."
        )
        return result
    raise ValueError("Thao tác không có trong danh mục")


DRILL_SQL = """
WITH diem AS (
    SELECT h.ma_hoc_sinh, m.ma_mon, m.ten_mon,
           COUNT(*) AS so_luot_thi,
           ROUND(AVG(f.diem_so), 2) AS diem_tb,
           SUM(f.so_cau_dung) AS so_cau_dung
    FROM fact_ket_qua_thi f
    JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
    JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
    JOIN dim_thoi_gian t ON t.date_key = f.date_key
    WHERE f.date_key > 0
    GROUP BY h.ma_hoc_sinh, m.ma_mon, m.ten_mon
),
chuyen AS (
    SELECT h.ma_hoc_sinh, m.ma_mon, m.ten_mon,
           COUNT(*) AS so_phien,
           ROUND(SUM(f.thoi_luong_phut), 1) AS tong_phut,
           SUM(f.so_video_da_xem) AS so_video,
           ROUND(AVG(f.diem_chuyen_can), 2) AS diem_cc
    FROM fact_chuyen_can f
    JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
    JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
    JOIN dim_thoi_gian t ON t.date_key = f.date_key
    WHERE f.date_key > 0
    GROUP BY h.ma_hoc_sinh, m.ma_mon, m.ten_mon
)
SELECT COALESCE(d.ma_hoc_sinh, c.ma_hoc_sinh) AS ma_hoc_sinh,
       cur.ho_ten,
       cur.lop AS lop_hien_tai,
       COALESCE(d.ten_mon, c.ten_mon) AS ten_mon,
       d.diem_tb, d.so_luot_thi,
       c.tong_phut, c.so_phien, c.diem_cc
FROM diem d
FULL OUTER JOIN chuyen c
  ON d.ma_hoc_sinh = c.ma_hoc_sinh AND d.ma_mon = c.ma_mon
LEFT JOIN dim_hoc_sinh cur
  ON cur.ma_hoc_sinh = COALESCE(d.ma_hoc_sinh, c.ma_hoc_sinh) AND cur.is_current = 1
"""


def drill_across(dw, lop: str = "", ma_mon: str = "", limit: int = 0) -> dict:
    sql = DRILL_SQL
    args = []
    filters = []
    if lop:
        filters.append("cur.lop = ?")
        args.append(lop)
    if ma_mon:
        filters.append("COALESCE(d.ma_mon, c.ma_mon) = ?")
        args.append(ma_mon)
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY 1, 4"
    found = [dict(row) for row in dw.execute(sql, args)]
    only_score = sum(1 for row in found if row["tong_phut"] is None)
    only_attend = sum(1 for row in found if row["diem_tb"] is None)
    both = sum(1 for row in found if row["diem_tb"] is not None and row["tong_phut"] is not None)
    shown = found[:limit] if limit else found
    specs = [
        ("ma_hoc_sinh", "Mã HS"),
        ("ho_ten", "Họ tên"),
        ("lop_hien_tai", "Lớp hiện tại"),
        ("ten_mon", "Môn"),
        ("diem_tb", "Điểm TB"),
        ("so_luot_thi", "Lượt thi"),
        ("tong_phut", "Phút học"),
        ("so_phien", "Số phiên"),
        ("diem_cc", "Điểm CC"),
    ]
    packed = _packs(shown, specs)
    packed.update(
        {
            "kieu": "bang",
            "thao_tac": "Drill-across",
            "sql": " ".join(DRILL_SQL.split()),
            "so_dong": len(found),
            "so_dong_hien": len(shown),
            "chi_co_diem": only_score,
            "chi_co_chuyen_can": only_attend,
            "ca_hai": both,
            "vi_du_nhan_ban": _fanout(dw),
            "mo_ta": (
                "Mỗi fact được GROUP BY về hạt mã học sinh × môn trước khi nối. "
                "FULL OUTER JOIN giữ học sinh chỉ có bài thi hoặc chỉ có phiên học. "
                "JOIN thẳng hai fact sẽ nhân số liệu vì lệch mức hạt."
            ),
        }
    )
    return packed


def _fanout(dw):
    pair = dw.execute(
        """
        WITH diem AS (
            SELECT h.ma_hoc_sinh, m.ma_mon, COUNT(*) AS so_luot, SUM(f.diem_so) AS tong_diem
            FROM fact_ket_qua_thi f
            JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
            JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
            WHERE h.hoc_sinh_key > 0
            GROUP BY h.ma_hoc_sinh, m.ma_mon
        ),
        cc AS (
            SELECT h.ma_hoc_sinh, m.ma_mon, COUNT(*) AS so_phien, SUM(f.thoi_luong_phut) AS tong_phut
            FROM fact_chuyen_can f
            JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
            JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
            WHERE h.hoc_sinh_key > 0
            GROUP BY h.ma_hoc_sinh, m.ma_mon
        )
        SELECT d.ma_hoc_sinh, d.ma_mon, d.so_luot, c.so_phien, d.tong_diem, c.tong_phut
        FROM diem d
        JOIN cc c ON c.ma_hoc_sinh = d.ma_hoc_sinh AND c.ma_mon = d.ma_mon
        WHERE d.so_luot > 1 AND c.so_phien > 1
        ORDER BY d.so_luot * c.so_phien DESC
        LIMIT 1
        """
    ).fetchone()
    if pair is None:
        return None
    pair = dict(pair)
    wrong = dw.execute(
        """
        SELECT COUNT(*) AS so_dong,
               ROUND(SUM(f1.diem_so), 2) AS tong_diem_nhan,
               ROUND(SUM(f2.thoi_luong_phut), 1) AS tong_phut_nhan
        FROM fact_ket_qua_thi f1
        JOIN dim_hoc_sinh h1 ON h1.hoc_sinh_key = f1.hoc_sinh_key
        JOIN dim_mon_hoc m ON m.mon_hoc_key = f1.mon_hoc_key
        JOIN fact_chuyen_can f2 ON f2.mon_hoc_key = f1.mon_hoc_key
        JOIN dim_hoc_sinh h2 ON h2.hoc_sinh_key = f2.hoc_sinh_key AND h2.ma_hoc_sinh = h1.ma_hoc_sinh
        WHERE h1.ma_hoc_sinh = ? AND m.ma_mon = ?
        """,
        (pair["ma_hoc_sinh"], pair["ma_mon"]),
    ).fetchone()
    wrong = dict(wrong)
    return {
        "ma_hoc_sinh": pair["ma_hoc_sinh"],
        "ma_mon": pair["ma_mon"],
        "so_luot_thi": pair["so_luot"],
        "so_phien": pair["so_phien"],
        "tong_diem_dung": round(pair["tong_diem"], 2),
        "tong_phut_dung": round(pair["tong_phut"], 1),
        "so_dong_khi_join_thang": wrong["so_dong"],
        "tong_diem_bi_nhan": wrong["tong_diem_nhan"],
        "tong_phut_bi_nhan": wrong["tong_phut_nhan"],
    }


def explain_plans(dw) -> dict:
    queries = {
        "khoa_ngoai_hoc_sinh": "SELECT * FROM fact_ket_qua_thi WHERE hoc_sinh_key = 1",
        "cot_phan_loai": "SELECT COUNT(*) FROM fact_ket_qua_thi WHERE loai_bai = N'THI'",
        "tang_tong_hop": "SELECT ten_mon, SUM(so_luot) FROM iv_diem_theo_mon_thang WITH (NOEXPAND) GROUP BY ten_mon",
    }
    indexes = [
        f"{row['bang']}.{row['ten_index']} ({row['kieu']})"
        for row in dw.execute(
            """
            SELECT t.name AS bang, i.name AS ten_index, i.type_desc AS kieu
            FROM sys.indexes i
            JOIN sys.objects t ON t.object_id = i.object_id
            WHERE i.name IS NOT NULL
              AND t.name IN (N'fact_ket_qua_thi', N'iv_diem_theo_mon_thang')
            ORDER BY t.name, i.index_id
            """
        )
    ]
    return {name: {"sql": sql, "ke_hoach": indexes or ["Chưa có chỉ mục"]} for name, sql in queries.items()}


def bench(dw, laps: int = 40) -> dict:
    summary_sql = """
        SELECT ten_mon, lop, SUM(so_luot), SUM(tong_diem) / SUM(so_luot)
        FROM iv_diem_theo_mon_thang WITH (NOEXPAND)
        GROUP BY ten_mon, lop
    """
    atomic_sql = """
        SELECT m.ten_mon, h.lop, COUNT(*), AVG(f.diem_so)
        FROM fact_ket_qua_thi f
        JOIN dim_mon_hoc m ON m.mon_hoc_key = f.mon_hoc_key
        JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
        GROUP BY m.ten_mon, h.lop
    """
    started = time.perf_counter()
    for _ in range(laps):
        dw.execute(summary_sql).fetchall()
    mid = time.perf_counter()
    for _ in range(laps):
        dw.execute(atomic_sql).fetchall()
    end = time.perf_counter()
    fact_rows = dw.execute("SELECT COUNT(*) FROM fact_ket_qua_thi").fetchone()[0]
    summary_rows = dw.execute("SELECT COUNT(*) FROM iv_diem_theo_mon_thang WITH (NOEXPAND)").fetchone()[0]
    return {
        "so_vong": laps,
        "summary_ms": round((mid - started) * 1000, 1),
        "atomic_ms": round((end - mid) * 1000, 1),
        "dong_fact": fact_rows,
        "dong_summary": summary_rows,
    }


def dashboard(oltp, dw) -> dict:
    exam = dw.execute("SELECT COUNT(*) n, ROUND(AVG(diem_so), 2) tb FROM fact_ket_qua_thi").fetchone()
    attend = dw.execute(
        "SELECT COUNT(*) n, ROUND(COALESCE(SUM(thoi_luong_phut), 0), 1) phut, ROUND(AVG(diem_chuyen_can), 2) tb FROM fact_chuyen_can"
    ).fetchone()
    versions = dw.execute("SELECT COUNT(*) FROM dim_hoc_sinh WHERE hoc_sinh_key > 0").fetchone()[0]
    current = dw.execute("SELECT COUNT(*) FROM dim_hoc_sinh WHERE is_current = 1 AND hoc_sinh_key > 0").fetchone()[0]
    rejected = dw.execute("SELECT COUNT(*) FROM etl_reject").fetchone()[0]
    unknown = dw.execute(
        "SELECT COUNT(*) FROM fact_ket_qua_thi WHERE hoc_sinh_key = -1"
    ).fetchone()[0] + dw.execute(
        "SELECT COUNT(*) FROM fact_chuyen_can WHERE hoc_sinh_key = -1"
    ).fetchone()[0]
    oltp_exam = oltp.execute("SELECT COUNT(*) FROM lan_lam_bai").fetchone()[0]
    oltp_session = oltp.execute("SELECT COUNT(*) FROM phien_hoc").fetchone()[0]
    summary_rows = dw.execute("SELECT COUNT(*) FROM iv_diem_theo_mon_thang WITH (NOEXPAND)").fetchone()[0]
    by_subject = [
        dict(row)
        for row in dw.execute(
            """
            SELECT ten_mon, SUM(so_luot) AS so_luot,
                   ROUND(SUM(tong_diem) / SUM(so_luot), 2) AS diem_tb
            FROM iv_diem_theo_mon_thang WITH (NOEXPAND)
            GROUP BY ten_mon
            ORDER BY diem_tb DESC
            """
        )
    ]
    by_day = [
        dict(row)
        for row in dw.execute(
            """
            SELECT t.ngay, COUNT(*) AS so_luot, ROUND(AVG(f.diem_so), 2) AS diem_tb
            FROM fact_ket_qua_thi f
            JOIN dim_thoi_gian t ON t.date_key = f.date_key
            WHERE t.date_key > 0
            GROUP BY t.ngay
            ORDER BY t.ngay DESC
            LIMIT 16
            """
        )
    ]
    by_day.reverse()
    last_batch = dw.execute("SELECT * FROM etl_batch ORDER BY batch_id DESC LIMIT 1").fetchone()
    return {
        "kpi": {
            "so_bai": exam["n"],
            "diem_tb": exam["tb"],
            "so_phien": attend["n"],
            "tong_phut": attend["phut"],
            "diem_cc": attend["tb"],
            "phien_ban_scd": versions,
            "hoc_sinh_hien_tai": current,
            "bi_loai": rejected,
            "unknown_member": unknown,
        },
        "pipeline": {
            "oltp_bai": oltp_exam,
            "oltp_phien": oltp_session,
            "fact_bai": exam["n"],
            "fact_phien": attend["n"],
            "bi_loai": rejected,
            "dong_summary": summary_rows,
        },
        "theo_mon": by_subject,
        "theo_ngay": by_day,
        "me_gan_nhat": dict(last_batch) if last_batch else None,
    }


def quality_report(dw) -> dict:
    total = dw.execute(
        """
        SELECT COALESCE(SUM(src_exam), 0) src_exam,
               COALESCE(SUM(loaded_exam), 0) loaded_exam,
               COALESCE(SUM(rejected_exam), 0) rejected_exam,
               COALESCE(SUM(unknown_exam), 0) unknown_exam,
               COALESCE(SUM(src_session), 0) src_session,
               COALESCE(SUM(loaded_session), 0) loaded_session,
               COALESCE(SUM(rejected_session), 0) rejected_session,
               COALESCE(SUM(scd_new), 0) scd_new
        FROM etl_batch
        """
    ).fetchone()
    fact_exam = dw.execute("SELECT COUNT(*) FROM fact_ket_qua_thi").fetchone()[0]
    fact_session = dw.execute("SELECT COUNT(*) FROM fact_chuyen_can").fetchone()[0]
    sum_exam = dw.execute("SELECT COALESCE(SUM(so_luot), 0) FROM iv_diem_theo_mon_thang WITH (NOEXPAND)").fetchone()[0]
    reject_exam = dw.execute("SELECT COUNT(*) FROM etl_reject WHERE nguon = 'lan_lam_bai'").fetchone()[0]
    batches = [dict(row) for row in dw.execute("SELECT * FROM etl_batch ORDER BY batch_id DESC LIMIT 12")]
    rejects = [
        dict(row)
        for row in dw.execute(
            "SELECT id, batch_id, nguon, nguon_id, ly_do, created_at FROM etl_reject ORDER BY id DESC LIMIT 20"
        )
    ]
    return {
        "tong": dict(total),
        "fact_bai": fact_exam,
        "fact_phien": fact_session,
        "summary_so_luot": sum_exam,
        "reject_bai": reject_exam,
        "khop_bai": total["loaded_exam"] == fact_exam and total["src_exam"] == total["loaded_exam"] + total["rejected_exam"],
        "khop_phien": total["loaded_session"] == fact_session and total["src_session"] == total["loaded_session"] + total["rejected_session"],
        "khop_summary": sum_exam == dw.execute("SELECT COUNT(*) FROM fact_ket_qua_thi WHERE date_key > 0").fetchone()[0],
        "me": batches,
        "loai": rejects,
    }


def student_history(dw, ma_hs: str) -> dict:
    versions = [
        dict(row)
        for row in dw.execute(
            """
            SELECT hoc_sinh_key, ma_hoc_sinh, ho_ten, lop, trang_thai_hoc_vu, ly_do,
                   start_date, end_date, is_current, version_no
            FROM dim_hoc_sinh
            WHERE ma_hoc_sinh = ?
            ORDER BY version_no
            """,
            (ma_hs,),
        )
    ]
    exams = [
        dict(row)
        for row in dw.execute(
            """
            SELECT t.ngay, f.diem_so, f.hoc_sinh_key, h.version_no, h.lop, h.trang_thai_hoc_vu, d.ten_de
            FROM fact_ket_qua_thi f
            JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
            JOIN dim_thoi_gian t ON t.date_key = f.date_key
            JOIN dim_de_thi d ON d.de_thi_key = f.de_thi_key
            WHERE h.ma_hoc_sinh = ?
            ORDER BY t.ngay DESC
            LIMIT 8
            """,
            (ma_hs,),
        )
    ]
    return {"phien_ban": versions, "bai_gan_day": exams}
