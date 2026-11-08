import random
import threading

from app.database import now_str, oltp_conn, oltp_lock
from app.grading import diem_chuyen_can
from app.hub import publish
from app.ingest import insert_exam, insert_session


class Simulator:
    def __init__(self):
        self._stop = threading.Event()
        self._thread = None
        self.running = False
        self.rng = random.Random()
        self.config = {
            "students_per_tick": 3,
            "interval_ms": 800,
            "include_bad": True,
            "include_members": False,
        }
        self.counts = {"bai": 0, "phien": 0, "ban": 0, "unknown": 0}

    def status(self) -> dict:
        return {"running": self.running, "config": dict(self.config), "counts": dict(self.counts)}

    def start(self, config: dict | None = None) -> dict:
        if config:
            self.config.update({k: v for k, v in config.items() if v is not None})
        if self.running:
            return self.status()
        self._stop.clear()
        self.running = True
        self._thread = threading.Thread(target=self._loop, name="simulator", daemon=True)
        self._thread.start()
        publish({"type": "simulator", "su_kien": "bat_dau", "config": self.config})
        return self.status()

    def stop(self) -> dict:
        was_running = self.running
        self._stop.set()
        self.running = False
        if self._thread and self._thread.is_alive() and threading.current_thread() is not self._thread:
            self._thread.join(timeout=5)
        if was_running:
            publish({"type": "simulator", "su_kien": "dung"})
        return self.status()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as exc:
                publish({"type": "error", "message": f"Bộ sinh dữ liệu: {exc}"})
            self._stop.wait(max(self.config["interval_ms"], 200) / 1000)
        self.running = False

    def _tick(self) -> None:
        with oltp_lock:
            conn = oltp_conn()
            try:
                students = [
                    dict(row)
                    for row in conn.execute("SELECT ma_hs, ho_ten FROM hoc_sinh")
                ]
                if not self.config.get("include_members"):
                    students = [row for row in students if not str(row["ma_hs"]).startswith("B23")]
                exams = [dict(row) for row in conn.execute("SELECT ma_de, thoi_gian_phut, so_cau FROM de_thi")]
                lessons = [
                    dict(row)
                    for row in conn.execute("SELECT ma_bai, thoi_luong_phut, loai_noi_dung FROM bai_hoc")
                ]
                if not students or not exams or not lessons:
                    return
                picked = self.rng.sample(students, k=min(self.config["students_per_tick"], len(students)))
                for student in picked:
                    if self.rng.random() < 0.4:
                        self._one_exam(conn, student, exams)
                    else:
                        self._one_session(conn, student, lessons)
                conn.commit()
            finally:
                conn.close()

    def _one_exam(self, conn, student, exams) -> None:
        exam = self.rng.choice(exams)
        total = exam["so_cau"] or 5
        roll = self.rng.random()
        stamp = now_str()
        if self.config.get("include_bad") and roll < 0.1:
            row = {
                "ma_hs": student["ma_hs"],
                "ma_de": exam["ma_de"],
                "nop_luc": stamp,
                "so_cau_dung": total + 3,
                "so_cau_sai": 1,
                "tong_so_cau": total,
                "diem": 15,
                "ty_le_dung": 0.2,
                "thoi_gian_giay": -4,
            }
            self.counts["ban"] += 1
            kind = "bai_ban"
        elif self.config.get("include_bad") and roll < 0.16:
            correct = self.rng.randint(0, total)
            row = {
                "ma_hs": "NGOAI_DS",
                "ma_de": exam["ma_de"],
                "nop_luc": stamp,
                "so_cau_dung": correct,
                "so_cau_sai": total - correct,
                "tong_so_cau": total,
                "diem": round(10 * correct / total, 2),
                "ty_le_dung": round(correct / total, 4),
                "thoi_gian_giay": self.rng.randint(90, exam["thoi_gian_phut"] * 60),
            }
            self.counts["unknown"] += 1
            kind = "ma_la"
        else:
            correct = sum(self.rng.random() < 0.72 for _ in range(total))
            row = {
                "ma_hs": student["ma_hs"],
                "ma_de": exam["ma_de"],
                "nop_luc": stamp,
                "so_cau_dung": correct,
                "so_cau_sai": total - correct,
                "tong_so_cau": total,
                "diem": round(10 * correct / total, 2),
                "ty_le_dung": round(correct / total, 4),
                "thoi_gian_giay": self.rng.randint(90, max(exam["thoi_gian_phut"] * 60, 120)),
            }
            self.counts["bai"] += 1
            kind = "nop_bai"
        insert_exam(conn, row)
        publish(
            {
                "type": "oltp",
                "nguon": "bo_sinh",
                "su_kien": kind,
                "ma_hs": row["ma_hs"],
                "ma_de": row["ma_de"],
                "diem": row["diem"],
                "luc": stamp,
            }
        )

    def _one_session(self, conn, student, lessons) -> None:
        lesson = self.rng.choice(lessons)
        stamp = now_str()
        if self.config.get("include_bad") and self.rng.random() < 0.05:
            row = {
                "ma_hs": student["ma_hs"],
                "ma_bai": lesson["ma_bai"],
                "ket_thuc_luc": stamp,
                "thoi_luong_giay": -30,
                "so_video": 3,
                "so_tuong_tac": -1,
                "diem_chuyen_can": 12,
            }
            self.counts["ban"] += 1
            kind = "phien_ban"
        else:
            ratio = self.rng.uniform(0.4, 1.0)
            duration = max(60, int(lesson["thoi_luong_phut"] * 60 * ratio))
            interactions = self.rng.randint(1, 10)
            video = 1 if lesson["loai_noi_dung"] == "VIDEO" and ratio >= 0.6 else 0
            row = {
                "ma_hs": student["ma_hs"],
                "ma_bai": lesson["ma_bai"],
                "ket_thuc_luc": stamp,
                "thoi_luong_giay": duration,
                "so_video": video,
                "so_tuong_tac": interactions,
                "diem_chuyen_can": diem_chuyen_can(duration, interactions, lesson["thoi_luong_phut"]),
            }
            self.counts["phien"] += 1
            kind = "phien_hoc"
        insert_session(conn, row)
        publish(
            {
                "type": "oltp",
                "nguon": "bo_sinh",
                "su_kien": kind,
                "ma_hs": row["ma_hs"],
                "ma_bai": row["ma_bai"],
                "luc": stamp,
            }
        )


simulator = Simulator()
