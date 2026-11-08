import threading
import time

import pyodbc
from datetime import date, timedelta

from app.database import date_key_of, dw_conn, dw_lock, now_str, oltp_conn, oltp_lock, rows
from app.ingest import dump_row

_stop = threading.Event()
_thread = None
END_OF_TIME = "9999-12-31 23:59:59"


def validate_exam(row: dict) -> list[str]:
    errors = []
    total = row["tong_so_cau"]
    correct = row["so_cau_dung"]
    wrong = row["so_cau_sai"]
    if total is None or total <= 0:
        errors.append("Tổng số câu không hợp lệ")
        return errors
    if correct < 0 or wrong < 0:
        errors.append("Số câu đúng hoặc sai bị âm")
    if correct + wrong != total:
        errors.append("Số câu đúng cộng số câu sai khác tổng số câu")
    if not 0 <= row["diem"] <= 10:
        errors.append("Điểm nằm ngoài đoạn 0 đến 10")
    else:
        expected = round(10 * correct / total, 2)
        if abs(row["diem"] - expected) > 0.05:
            errors.append("Điểm không khớp số câu đúng")
    expected_rate = round(correct / total, 4)
    if abs(row["ty_le_dung"] - expected_rate) > 0.02:
        errors.append("Tỷ lệ đúng không khớp số câu")
    if row["thoi_gian_giay"] <= 0 or row["thoi_gian_giay"] > 4 * 3600:
        errors.append("Thời gian làm bài bất thường")
    return errors


def validate_session(row: dict) -> list[str]:
    errors = []
    if row["thoi_luong_giay"] <= 0 or row["thoi_luong_giay"] > 8 * 3600:
        errors.append("Thời lượng phiên học bất thường")
    if row["so_video"] not in (0, 1):
        errors.append("Số video đã xem phải là 0 hoặc 1")
    if row["so_tuong_tac"] < 0 or row["so_tuong_tac"] > 200:
        errors.append("Số tương tác ngoài khoảng cho phép")
    if not 0 <= row["diem_chuyen_can"] <= 10:
        errors.append("Điểm chuyên cần nằm ngoài đoạn 0 đến 10")
    return errors


def _next_key(dw, table: str, column: str) -> int:
    found = dw.execute(
        f'SELECT COALESCE(MAX("{column}"), 0) + 1 FROM "{table}" WHERE "{column}" > 0'
    ).fetchone()
    return found[0]


def _reject(dw, batch_id, source, source_id, reason, payload) -> None:
    dw.execute(
        """
        INSERT INTO etl_reject (batch_id, nguon, nguon_id, ly_do, du_lieu, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (batch_id, source, source_id, reason, dump_row(payload), now_str()),
    )


def ensure_unknown(dw) -> None:
    dw.execute(
        """
        INSERT OR IGNORE INTO dim_hoc_sinh (
            hoc_sinh_key, ma_hoc_sinh, ho_ten, ngay_sinh, lop, trang_thai_hoc_vu,
            ly_do, start_date, end_date, is_current, version_no
        ) VALUES (-1, 'UNKNOWN', 'Không xác định', NULL, 'N/A', 'KHONG_XAC_DINH',
                  'UNKNOWN', '1900-01-01 00:00:00', ?, 1, 0)
        """,
        (END_OF_TIME,),
    )
    dw.execute(
        """
        INSERT OR IGNORE INTO dim_mon_hoc (mon_hoc_key, ma_mon, ten_mon, so_tin_chi, khoa)
        VALUES (-1, 'UNKNOWN', 'Không xác định', 0, 'N/A')
        """
    )
    dw.execute(
        """
        INSERT OR IGNORE INTO dim_de_thi (de_thi_key, ma_de, ten_de, loai, do_kho, so_cau, ma_mon)
        VALUES (-1, 'UNKNOWN', 'Không xác định', 'KHONG_XAC_DINH', 'N/A', 0, 'UNKNOWN')
        """
    )
    dw.execute(
        """
        INSERT OR IGNORE INTO dim_bai_hoc (
            bai_hoc_key, ma_bai, ten_bai, loai_noi_dung, thoi_luong_phut, ma_mon
        ) VALUES (-1, 'UNKNOWN', 'Không xác định', 'KHONG_XAC_DINH', 0, 'UNKNOWN')
        """
    )
    dw.execute(
        """
        INSERT OR IGNORE INTO dim_thoi_gian (
            date_key, ngay, thu, tuan, thang, ten_thang, quy, nam, hoc_ky, nam_hoc
        ) VALUES (-1, NULL, 'N/A', 0, 0, 'N/A', 0, 0, 'N/A', 'N/A')
        """
    )


def _academic(day: date):
    if day.month >= 8:
        return "HK1", f"{day.year}-{day.year + 1}"
    if day.month == 1:
        return "HK1", f"{day.year - 1}-{day.year}"
    if day.month == 7:
        return "HE", f"{day.year - 1}-{day.year}"
    return "HK2", f"{day.year - 1}-{day.year}"


def ensure_calendar(dw) -> None:
    existing = dw.execute("SELECT COUNT(*) FROM dim_thoi_gian WHERE date_key > 0").fetchone()[0]
    if existing > 300:
        return
    weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    start = date(2026, 8, 1)
    end = date(2027, 6, 30)
    payload = []
    day = start
    while day <= end:
        hoc_ky, nam_hoc = _academic(day)
        payload.append(
            (
                day.year * 10000 + day.month * 100 + day.day,
                day.isoformat(),
                weekdays[day.weekday()],
                int(day.strftime("%V")),
                day.month,
                f"Tháng {day.month}",
                (day.month - 1) // 3 + 1,
                day.year,
                hoc_ky,
                nam_hoc,
            )
        )
        day += timedelta(days=1)
    dw.executemany(
        """
        INSERT INTO dim_thoi_gian (
            date_key, ngay, thu, tuan, thang, ten_thang, quy, nam, hoc_ky, nam_hoc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )


def _upsert(dw, table, key_col, business_col, business, values: dict) -> None:
    found = dw.execute(
        f'SELECT "{key_col}" FROM "{table}" WHERE "{business_col}" = ?',
        (business,),
    ).fetchone()
    if found:
        sets = ", ".join(f'"{col}" = ?' for col in values)
        dw.execute(
            f'UPDATE "{table}" SET {sets} WHERE "{key_col}" = ?',
            (*values.values(), found[0]),
        )
        return
    values = {key_col: _next_key(dw, table, key_col), business_col: business, **values}
    cols = ", ".join(f'"{col}"' for col in values)
    marks = ", ".join("?" for _ in values)
    dw.execute(f'INSERT INTO "{table}" ({cols}) VALUES ({marks})', tuple(values.values()))


def sync_dimensions(dw, subjects, exams, lessons) -> None:
    for subject in subjects:
        _upsert(
            dw,
            "dim_mon_hoc",
            "mon_hoc_key",
            "ma_mon",
            subject["ma_mon"],
            {"ten_mon": subject["ten_mon"], "so_tin_chi": subject["so_tin_chi"], "khoa": subject["khoa"]},
        )
    for exam in exams:
        _upsert(
            dw,
            "dim_de_thi",
            "de_thi_key",
            "ma_de",
            exam["ma_de"],
            {
                "ten_de": exam["ten_de"],
                "loai": exam["loai"],
                "do_kho": exam["do_kho"],
                "so_cau": exam["so_cau"],
                "ma_mon": exam["ma_mon"],
            },
        )
    for lesson in lessons:
        _upsert(
            dw,
            "dim_bai_hoc",
            "bai_hoc_key",
            "ma_bai",
            lesson["ma_bai"],
            {
                "ten_bai": lesson["ten_bai"],
                "loai_noi_dung": lesson["loai_noi_dung"],
                "thoi_luong_phut": lesson["thoi_luong_phut"],
                "ma_mon": lesson["ma_mon"],
            },
        )


def apply_scd(dw, event, students) -> bool:
    student = students.get(event["ma_hs"])
    if student is None:
        return False
    current = dw.execute(
        "SELECT * FROM dim_hoc_sinh WHERE ma_hoc_sinh = ? AND is_current = 1",
        (event["ma_hs"],),
    ).fetchone()
    if current is None:
        dw.execute(
            """
            INSERT INTO dim_hoc_sinh (
                hoc_sinh_key, ma_hoc_sinh, ho_ten, ngay_sinh, lop, trang_thai_hoc_vu,
                ly_do, start_date, end_date, is_current, version_no
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
            """,
            (
                _next_key(dw, "dim_hoc_sinh", "hoc_sinh_key"),
                event["ma_hs"],
                student["ho_ten"],
                student["ngay_sinh"],
                event["lop_moi"],
                event["trang_thai_moi"],
                event["ly_do"],
                event["thoi_diem"],
                END_OF_TIME,
            ),
        )
        return True
    if current["lop"] == event["lop_moi"] and current["trang_thai_hoc_vu"] == event["trang_thai_moi"]:
        return False
    dw.execute(
        "UPDATE dim_hoc_sinh SET end_date = ?, is_current = 0 WHERE hoc_sinh_key = ?",
        (event["thoi_diem"], current["hoc_sinh_key"]),
    )
    dw.execute(
        """
        INSERT INTO dim_hoc_sinh (
            hoc_sinh_key, ma_hoc_sinh, ho_ten, ngay_sinh, lop, trang_thai_hoc_vu,
            ly_do, start_date, end_date, is_current, version_no
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            _next_key(dw, "dim_hoc_sinh", "hoc_sinh_key"),
            event["ma_hs"],
            student["ho_ten"],
            student["ngay_sinh"],
            event["lop_moi"],
            event["trang_thai_moi"],
            event["ly_do"],
            event["thoi_diem"],
            END_OF_TIME,
            current["version_no"] + 1,
        ),
    )
    return True


def lookup_student(dw, ma_hs: str, at: str) -> int:
    if not ma_hs:
        return -1
    found = dw.execute(
        """
        SELECT hoc_sinh_key FROM dim_hoc_sinh
        WHERE ma_hoc_sinh = ? AND start_date <= ? AND end_date > ?
        ORDER BY start_date DESC
        LIMIT 1
        """,
        (ma_hs, at, at),
    ).fetchone()
    return found["hoc_sinh_key"] if found else -1


def _insert_or_reject(dw, sql, params, batch_id, source, source_id, payload) -> bool:
    dw.execute("SAVEPOINT fact_row")
    try:
        dw.execute(sql, params)
        dw.execute("RELEASE SAVEPOINT fact_row")
        return True
    except pyodbc.IntegrityError as exc:
        dw.execute("ROLLBACK TO SAVEPOINT fact_row")
        dw.execute("RELEASE SAVEPOINT fact_row")
        _reject(dw, batch_id, source, source_id, f"Vi phạm ràng buộc kho: {exc}", payload)
        return False


def refresh_summaries(_dw) -> None:
    """Indexed view tự bảo trì khi fact thay đổi. Dashboard đọc iv_* và vw_*."""
    return


def _watermark(dw, stream: str) -> int:
    found = dw.execute("SELECT last_id FROM etl_watermark WHERE stream = ?", (stream,)).fetchone()
    return found["last_id"] if found else 0


def _set_watermark(dw, stream: str, last_id: int) -> None:
    found = dw.execute("SELECT last_id FROM etl_watermark WHERE stream = ?", (stream,)).fetchone()
    if found:
        dw.execute("UPDATE etl_watermark SET last_id = ? WHERE stream = ?", (last_id, stream))
        return
    dw.execute("INSERT INTO etl_watermark(stream, last_id) VALUES (?, ?)", (stream, last_id))


def run_batch(trigger: str = "tu_dong") -> dict:
    started = time.perf_counter()
    with dw_lock:
        dw = dw_conn()
        try:
            ensure_unknown(dw)
            ensure_calendar(dw)
            mark_exam = _watermark(dw, "lan_lam_bai")
            mark_session = _watermark(dw, "phien_hoc")
            mark_event = _watermark(dw, "su_kien_hoc_vu")
            with oltp_lock:
                oltp = oltp_conn()
                try:
                    subjects = rows(oltp, "SELECT * FROM mon_hoc")
                    exams = rows(oltp, "SELECT * FROM de_thi")
                    lessons = rows(oltp, "SELECT * FROM bai_hoc")
                    students = {row["ma_hs"]: row for row in rows(oltp, "SELECT * FROM hoc_sinh")}
                    exam_rows = rows(
                        oltp,
                        """
                        SELECT * FROM lan_lam_bai
                        WHERE id > ? AND trang_thai = 'DA_NOP'
                        ORDER BY id
                        """,
                        (mark_exam,),
                    )
                    session_rows = rows(
                        oltp,
                        """
                        SELECT * FROM phien_hoc
                        WHERE id > ? AND trang_thai = 'HOAN_THANH'
                        ORDER BY id
                        """,
                        (mark_session,),
                    )
                    events = rows(
                        oltp,
                        "SELECT * FROM su_kien_hoc_vu WHERE id > ? ORDER BY id",
                        (mark_event,),
                    )
                finally:
                    oltp.close()

            if not exam_rows and not session_rows and not events:
                dw.commit()
                return {"touched": False, "trigger": trigger}

            sync_dimensions(dw, subjects, exams, lessons)
            de_map = {row["ma_de"]: row for row in rows(dw, "SELECT * FROM dim_de_thi")}
            bai_map = {row["ma_bai"]: row for row in rows(dw, "SELECT * FROM dim_bai_hoc")}
            mon_map = {row["ma_mon"]: row["mon_hoc_key"] for row in rows(dw, "SELECT ma_mon, mon_hoc_key FROM dim_mon_hoc")}
            dates = {row["date_key"] for row in rows(dw, "SELECT date_key FROM dim_thoi_gian")}

            cur = dw.execute(
                "INSERT INTO etl_batch (trigger_name, started_at, status) VALUES (?, ?, 'DANG_CHAY')",
                (trigger, now_str()),
            )
            batch_id = cur.lastrowid
            scd_new = 0
            max_event = mark_event
            for event in events:
                max_event = event["id"]
                if apply_scd(dw, event, students):
                    scd_new += 1
                else:
                    if event["ma_hs"] not in students:
                        _reject(dw, batch_id, "su_kien_hoc_vu", event["id"], "Không thấy học sinh trong OLTP", event)

            loaded_exam = rejected_exam = unknown_exam = 0
            max_exam = mark_exam
            for row in exam_rows:
                max_exam = row["id"]
                reasons = validate_exam(row)
                if reasons:
                    _reject(dw, batch_id, "lan_lam_bai", row["id"], "; ".join(reasons), row)
                    rejected_exam += 1
                    continue
                hs_key = lookup_student(dw, row["ma_hs"], row["nop_luc"])
                exam = de_map.get(row["ma_de"])
                if exam is None:
                    de_key, mon_key, loai = -1, -1, "KHONG_XAC_DINH"
                else:
                    de_key = exam["de_thi_key"]
                    mon_key = mon_map.get(exam["ma_mon"], -1)
                    loai = exam["loai"]
                date_key = date_key_of(row["nop_luc"])
                if date_key not in dates:
                    date_key = -1
                ok = _insert_or_reject(
                    dw,
                    """
                    INSERT INTO fact_ket_qua_thi (
                        lan_lam_id, hoc_sinh_key, date_key, mon_hoc_key, de_thi_key,
                        diem_so, so_cau_dung, so_cau_sai, tong_so_cau, ty_le_dung,
                        thoi_gian_lam_giay, loai_bai
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        hs_key,
                        date_key,
                        mon_key,
                        de_key,
                        row["diem"],
                        row["so_cau_dung"],
                        row["so_cau_sai"],
                        row["tong_so_cau"],
                        row["ty_le_dung"],
                        row["thoi_gian_giay"],
                        loai,
                    ),
                    batch_id,
                    "lan_lam_bai",
                    row["id"],
                    row,
                )
                if not ok:
                    rejected_exam += 1
                    continue
                loaded_exam += 1
                if hs_key == -1:
                    unknown_exam += 1

            loaded_session = rejected_session = unknown_session = 0
            max_session = mark_session
            for row in session_rows:
                max_session = row["id"]
                reasons = validate_session(row)
                if reasons:
                    _reject(dw, batch_id, "phien_hoc", row["id"], "; ".join(reasons), row)
                    rejected_session += 1
                    continue
                hs_key = lookup_student(dw, row["ma_hs"], row["ket_thuc_luc"])
                lesson = bai_map.get(row["ma_bai"])
                if lesson is None:
                    bai_key, mon_key, loai = -1, -1, "KHONG_XAC_DINH"
                else:
                    bai_key = lesson["bai_hoc_key"]
                    mon_key = mon_map.get(lesson["ma_mon"], -1)
                    loai = lesson["loai_noi_dung"]
                date_key = date_key_of(row["ket_thuc_luc"])
                if date_key not in dates:
                    date_key = -1
                ok = _insert_or_reject(
                    dw,
                    """
                    INSERT INTO fact_chuyen_can (
                        phien_hoc_id, hoc_sinh_key, date_key, mon_hoc_key, bai_hoc_key,
                        thoi_luong_phut, so_video_da_xem, so_tuong_tac, diem_chuyen_can, loai_noi_dung
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        hs_key,
                        date_key,
                        mon_key,
                        bai_key,
                        round(row["thoi_luong_giay"] / 60, 2),
                        row["so_video"],
                        row["so_tuong_tac"],
                        row["diem_chuyen_can"],
                        loai,
                    ),
                    batch_id,
                    "phien_hoc",
                    row["id"],
                    row,
                )
                if not ok:
                    rejected_session += 1
                    continue
                loaded_session += 1
                if hs_key == -1:
                    unknown_session += 1

            if exam_rows or session_rows:
                refresh_summaries(dw)
            _set_watermark(dw, "lan_lam_bai", max_exam)
            _set_watermark(dw, "phien_hoc", max_session)
            _set_watermark(dw, "su_kien_hoc_vu", max_event)
            duration = int((time.perf_counter() - started) * 1000)
            dw.execute(
                """
                UPDATE etl_batch SET
                    finished_at = ?, duration_ms = ?, src_exam = ?, loaded_exam = ?,
                    rejected_exam = ?, unknown_exam = ?, src_session = ?, loaded_session = ?,
                    rejected_session = ?, unknown_session = ?, src_event = ?, scd_new = ?, status = 'XONG'
                WHERE batch_id = ?
                """,
                (
                    now_str(),
                    duration,
                    len(exam_rows),
                    loaded_exam,
                    rejected_exam,
                    unknown_exam,
                    len(session_rows),
                    loaded_session,
                    rejected_session,
                    unknown_session,
                    len(events),
                    scd_new,
                    batch_id,
                ),
            )
            dw.commit()
            result = {
                "touched": True,
                "trigger": trigger,
                "batch_id": batch_id,
                "src_exam": len(exam_rows),
                "loaded_exam": loaded_exam,
                "rejected_exam": rejected_exam,
                "unknown_exam": unknown_exam,
                "src_session": len(session_rows),
                "loaded_session": loaded_session,
                "rejected_session": rejected_session,
                "unknown_session": unknown_session,
                "src_event": len(events),
                "scd_new": scd_new,
                "duration_ms": duration,
            }
        except Exception:
            dw.rollback()
            raise
        finally:
            dw.close()
    return result


def etl_loop() -> None:
    from app import hub

    while not _stop.is_set():
        try:
            stats = run_batch("tu_dong")
            if stats.get("touched"):
                hub.publish({"type": "etl", **stats})
        except Exception as exc:
            hub.publish({"type": "error", "message": str(exc)})
        _stop.wait(1.2)


def start_etl() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=etl_loop, name="etl", daemon=True)
    _thread.start()


def stop_etl() -> None:
    _stop.set()
    if _thread and _thread.is_alive() and threading.current_thread() is not _thread:
        _thread.join(timeout=8)
