import random
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import dw_conn, dw_lock, init_schemas, oltp_conn, oltp_lock, wipe
from app.grading import diem_chuyen_can
from mockup_generator.mau import (
    CLASSES,
    DEM,
    ENROLL_AT,
    HO,
    LESSONS,
    PEOPLE,
    QUESTIONS,
    SCD_AT,
    SUBJECTS,
    TEN,
    exams_for_subject,
)


def _unique_name(rng: random.Random, used: set) -> str:
    for _ in range(50):
        name = f"{rng.choice(HO)} {rng.choice(DEM)} {rng.choice(TEN)}"
        if name not in used:
            used.add(name)
            return name
    name = f"Học sinh {len(used) + 1}"
    used.add(name)
    return name


def build_roster(rng: random.Random):
    roster = []
    for person in PEOPLE:
        ma, ten, birth, lop_goc, lop_now, status, role = person
        roster.append(
            {
                "ma_hs": ma,
                "ho_ten": ten,
                "ngay_sinh": birth,
                "lop_goc": lop_goc,
                "lop": lop_now,
                "trang_thai": status,
                "vai_tro": role,
            }
        )
    counts = Counter(item["lop_goc"] for item in roster)
    used = {item["ho_ten"] for item in roster}
    seq = 1
    while any(counts[lop] < 12 for lop in CLASSES):
        for lop in CLASSES:
            if counts[lop] >= 12:
                continue
            month = (seq % 12) + 1
            day = (seq % 27) + 1
            roster.append(
                {
                    "ma_hs": f"HS{seq:03d}",
                    "ho_ten": _unique_name(rng, used),
                    "ngay_sinh": f"2005-{month:02d}-{day:02d}",
                    "lop_goc": lop,
                    "lop": lop,
                    "trang_thai": "DANG_HOC",
                    "vai_tro": "",
                }
            )
            counts[lop] += 1
            seq += 1
    return roster


def _weekdays(start: date, end: date):
    day = start
    while day <= end:
        if day.weekday() < 5:
            yield day
        day += timedelta(days=1)


def _reason(person: dict) -> str:
    if person["trang_thai"] == "BAO_LUU":
        return "BAO_LUU"
    if person["trang_thai"] == "CANH_BAO_HOC_VU":
        return "CANH_BAO_HOC_VU"
    if person["lop"] != person["lop_goc"]:
        return "CHUYEN_LOP"
    return "NHAP_HOC"


def seed_if_empty() -> bool:
    with oltp_lock:
        conn = oltp_conn()
        try:
            count = conn.execute("SELECT COUNT(*) FROM hoc_sinh").fetchone()[0]
            if count:
                return False
            _fill(conn)
            conn.commit()
            return True
        finally:
            conn.close()


def _fill(conn) -> None:
    rng = random.Random(9)
    roster = build_roster(rng)
    conn.executemany(
        "INSERT INTO mon_hoc (ma_mon, ten_mon, so_tin_chi, khoa) VALUES (?, ?, ?, ?)",
        SUBJECTS,
    )
    exams = []
    for ma, _ten, _tin, _khoa in SUBJECTS:
        exams.extend(exams_for_subject(ma))
    conn.executemany(
        """
        INSERT INTO de_thi (ma_de, ma_mon, ten_de, loai, do_kho, so_cau, thoi_gian_phut)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        exams,
    )
    question_rows = []
    for ma_mon, bank in QUESTIONS.items():
        for exam in exams_for_subject(ma_mon):
            ma_de = exam[0]
            for content, a, b, c, d, answer in bank:
                question_rows.append((ma_de, content, a, b, c, d, answer))
    conn.executemany(
        """
        INSERT INTO cau_hoi (
            ma_de, noi_dung, phuong_an_a, phuong_an_b, phuong_an_c, phuong_an_d, dap_an_dung
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        question_rows,
    )
    conn.executemany(
        """
        INSERT INTO bai_hoc (ma_bai, ma_mon, ten_bai, loai_noi_dung, thoi_luong_phut)
        VALUES (?, ?, ?, ?, ?)
        """,
        LESSONS,
    )
    conn.executemany(
        """
        INSERT INTO hoc_sinh (
            ma_hs, ho_ten, ngay_sinh, email, lop, trang_thai_hoc_vu, ngay_vao_hoc, vai_tro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                person["ma_hs"],
                person["ho_ten"],
                person["ngay_sinh"],
                f"{person['ma_hs'].lower()}@ptit.edu.vn",
                person["lop"],
                person["trang_thai"],
                ENROLL_AT[:10],
                person["vai_tro"],
            )
            for person in roster
        ],
    )

    events = []
    for person in roster:
        events.append((person["ma_hs"], ENROLL_AT, person["lop_goc"], "DANG_HOC", "NHAP_HOC"))
    for person in roster:
        if person["lop"] != person["lop_goc"] or person["trang_thai"] != "DANG_HOC":
            events.append(
                (person["ma_hs"], SCD_AT, person["lop"], person["trang_thai"], _reason(person))
            )
    conn.executemany(
        """
        INSERT INTO su_kien_hoc_vu (ma_hs, thoi_diem, lop_moi, trang_thai_moi, ly_do)
        VALUES (?, ?, ?, ?, ?)
        """,
        events,
    )

    lessons = [
        {"ma_bai": item[0], "thoi_luong_phut": item[4], "loai_noi_dung": item[3]}
        for item in LESSONS
    ]
    exam_rows = [{"ma_de": item[0], "thoi_gian_phut": item[6]} for item in exams]
    sessions = []
    attempts = []

    def add_session(ma_hs, lesson, when, ratio, interactions):
        duration = max(60, int(lesson["thoi_luong_phut"] * 60 * ratio))
        video = 1 if lesson["loai_noi_dung"] == "VIDEO" and ratio >= 0.6 else 0
        sessions.append(
            (
                ma_hs,
                lesson["ma_bai"],
                when,
                duration,
                video,
                interactions,
                diem_chuyen_can(duration, interactions, lesson["thoi_luong_phut"]),
                "HOAN_THANH",
            )
        )

    def add_exam(ma_hs, exam, when, correct):
        total = 5
        wrong = total - correct
        attempts.append(
            (
                ma_hs,
                exam["ma_de"],
                when,
                correct,
                wrong,
                total,
                round(10 * correct / total, 2),
                round(correct / total, 4),
                rng.randint(150, exam["thoi_gian_phut"] * 60),
                "DA_NOP",
            )
        )

    for person in roster:
        for day in _weekdays(date(2026, 9, 8), date(2026, 11, 3)):
            stamp = f"{day.isoformat()} {rng.randint(7, 20):02d}:{rng.randint(0, 59):02d}:00"
            if person["vai_tro"] != "chi_thi" and rng.random() < 0.42:
                add_session(person["ma_hs"], rng.choice(lessons), stamp, rng.uniform(0.35, 1.05), rng.randint(1, 12))
            if person["vai_tro"] != "chi_hoc" and rng.random() < 0.16:
                add_exam(person["ma_hs"], rng.choice(exam_rows), stamp, sum(rng.random() < rng.uniform(0.4, 0.95) for _ in range(5)))

    lesson_csdl = next(item for item in lessons if item["ma_bai"] == "CSDL_B1")
    exam_csdl = next(item for item in exam_rows if item["ma_de"] == "CSDL_T1")
    for person in roster:
        if person["vai_tro"] not in {"thanh_vien", "bao_luu", "canh_bao", "chi_hoc", "chi_thi"}:
            continue
        if person["vai_tro"] != "chi_thi":
            add_session(person["ma_hs"], lesson_csdl, "2026-09-18 14:00:00", 0.9, 6)
            add_session(person["ma_hs"], lesson_csdl, "2026-10-20 14:10:00", 0.8, 5)
        if person["vai_tro"] != "chi_hoc":
            add_exam(person["ma_hs"], exam_csdl, "2026-09-18 09:30:00", 4)
            add_exam(person["ma_hs"], exam_csdl, "2026-10-20 09:40:00", 3)

    conn.executemany(
        """
        INSERT INTO phien_hoc (
            ma_hs, ma_bai, ket_thuc_luc, thoi_luong_giay, so_video,
            so_tuong_tac, diem_chuyen_can, trang_thai
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sessions,
    )
    conn.executemany(
        """
        INSERT INTO lan_lam_bai (
            ma_hs, ma_de, nop_luc, so_cau_dung, so_cau_sai, tong_so_cau,
            diem, ty_le_dung, thoi_gian_giay, trang_thai
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        attempts,
    )


def nap_mau() -> None:
    """Xóa kỳ mẫu cũ, nạp lại OLTP rồi chạy ETL sang kho."""
    from app.etl import run_batch

    init_schemas()
    with oltp_lock:
        conn = oltp_conn()
        try:
            wipe(conn)
        finally:
            conn.close()
    with dw_lock:
        dw = dw_conn()
        try:
            wipe(dw)
        finally:
            dw.close()
    init_schemas()
    if not seed_if_empty():
        raise SystemExit("OLTP vẫn còn học sinh sau khi xóa")
    stats = run_batch("mau")
    oltp = oltp_conn()
    dw = dw_conn()
    try:
        exams = oltp.execute("SELECT COUNT(*) FROM lan_lam_bai").fetchone()[0]
        sessions = oltp.execute("SELECT COUNT(*) FROM phien_hoc").fetchone()[0]
        events = oltp.execute("SELECT COUNT(*) FROM su_kien_hoc_vu").fetchone()[0]
        facts = dw.execute("SELECT COUNT(*) FROM fact_ket_qua_thi").fetchone()[0]
        attend = dw.execute("SELECT COUNT(*) FROM fact_chuyen_can").fetchone()[0]
    finally:
        oltp.close()
        dw.close()
    print(f"OLTP: {exams} bài thi, {sessions} phiên học, {events} sự kiện học vụ")
    print(f"DW: {facts} fact bài thi, {attend} fact chuyên cần, ETL {stats.get('duration_ms')} ms")


if __name__ == "__main__":
    nap_mau()
