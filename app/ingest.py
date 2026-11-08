import json


def insert_exam(conn, row: dict) -> int:
    cur = conn.execute(
        """
        INSERT INTO lan_lam_bai (
            ma_hs, ma_de, nop_luc, so_cau_dung, so_cau_sai, tong_so_cau,
            diem, ty_le_dung, thoi_gian_giay, trang_thai
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["ma_hs"],
            row["ma_de"],
            row["nop_luc"],
            row["so_cau_dung"],
            row["so_cau_sai"],
            row["tong_so_cau"],
            row["diem"],
            row["ty_le_dung"],
            row["thoi_gian_giay"],
            row.get("trang_thai", "DA_NOP"),
        ),
    )
    return cur.lastrowid


def insert_session(conn, row: dict) -> int:
    cur = conn.execute(
        """
        INSERT INTO phien_hoc (
            ma_hs, ma_bai, ket_thuc_luc, thoi_luong_giay, so_video,
            so_tuong_tac, diem_chuyen_can, trang_thai
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["ma_hs"],
            row["ma_bai"],
            row["ket_thuc_luc"],
            row["thoi_luong_giay"],
            row["so_video"],
            row["so_tuong_tac"],
            row["diem_chuyen_can"],
            row.get("trang_thai", "HOAN_THANH"),
        ),
    )
    return cur.lastrowid


def insert_event(conn, row: dict) -> int:
    cur = conn.execute(
        """
        INSERT INTO su_kien_hoc_vu (ma_hs, thoi_diem, lop_moi, trang_thai_moi, ly_do)
        VALUES (?, ?, ?, ?, ?)
        """,
        (row["ma_hs"], row["thoi_diem"], row["lop_moi"], row["trang_thai_moi"], row["ly_do"]),
    )
    return cur.lastrowid


def dump_row(row) -> str:
    if isinstance(row, dict):
        return json.dumps(row, ensure_ascii=False, default=str)
    return json.dumps(dict(row), ensure_ascii=False, default=str)
