import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.database import dw_conn, dw_lock, init_schemas, now_str, oltp_conn, oltp_lock, rows, wipe
from app.etl import run_batch, start_etl, stop_etl
from app.grading import diem_chuyen_can, grade
from app.hub import bind_loop, clear as clear_hub, clients, publish, snapshot
from app.ingest import insert_event, insert_exam
from app.olap import bench, dashboard, drill_across, explain_plans, preset, quality_report, query_grouped, query_pivot, student_history
from app.simulator import simulator

STATIC = Path(__file__).resolve().parent / "static"
STATUSES = {"DANG_HOC", "BAO_LUU", "CANH_BAO_HOC_VU"}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    bind_loop(asyncio.get_running_loop())
    init_schemas()
    start_etl()
    print("LearnWH dang chay: http://127.0.0.1:8000")
    yield
    stop_etl()
    simulator.stop()


app = FastAPI(title="LearnWH", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class NopBai(BaseModel):
    ma_hs: str
    ma_de: str
    answers: dict[str, str]
    thoi_gian_giay: int = Field(ge=1, le=14400)


class PhienHoc(BaseModel):
    ma_hs: str
    ma_bai: str
    thoi_luong_giay: int = Field(ge=1, le=8 * 3600)
    so_tuong_tac: int = Field(ge=0, le=200)


class HocVu(BaseModel):
    ma_hs: str
    lop: str = Field(min_length=2, max_length=30)
    trang_thai: str
    ly_do: str = ""


class SimConfig(BaseModel):
    students_per_tick: int = Field(default=3, ge=1, le=20)
    interval_ms: int = Field(default=800, ge=200, le=5000)
    include_bad: bool = True
    include_members: bool = False


class OlapBody(BaseModel):
    nguon: str = "ket_qua"
    muc: str = "thang"
    ma_mon: str = ""
    lop: str = ""
    loai: str = ""
    tu_ngay: str = ""
    den_ngay: str = ""
    hang: str = "lop"
    cot: str = "mon"
    thao_tac: str = "Tuy chinh"
    kieu: str = "bang"
    hoc_ky: str = ""
    nam_hoc: str = ""


class ResetBody(BaseModel):
    xac_nhan: str


def _reason(old: dict, new_lop: str, new_status: str, given: str) -> str:
    if given.strip():
        return given.strip()
    if new_status == "BAO_LUU" and old["trang_thai_hoc_vu"] != "BAO_LUU":
        return "BAO_LUU"
    if new_status == "CANH_BAO_HOC_VU" and old["trang_thai_hoc_vu"] != "CANH_BAO_HOC_VU":
        return "CANH_BAO_HOC_VU"
    if new_status == "DANG_HOC" and old["trang_thai_hoc_vu"] != "DANG_HOC":
        return "QUAY_LAI_HOC"
    if new_lop != old["lop"]:
        return "CHUYEN_LOP"
    return "CAP_NHAT"


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/meta")
def meta():
    with oltp_lock:
        conn = oltp_conn()
        try:
            students = rows(
                conn,
                """
                SELECT ma_hs, ho_ten, lop, trang_thai_hoc_vu, COALESCE(vai_tro, N'') AS vai_tro
                FROM hoc_sinh ORDER BY ho_ten
                """,
            )
            classes = rows(conn, "SELECT DISTINCT lop FROM hoc_sinh ORDER BY lop")
            subjects = rows(conn, "SELECT ma_mon, ten_mon FROM mon_hoc ORDER BY ten_mon")
            exams = rows(conn, "SELECT ma_de, ma_mon, ten_de, loai, do_kho, so_cau, thoi_gian_phut FROM de_thi ORDER BY ten_de")
            lessons = rows(conn, "SELECT ma_bai, ma_mon, ten_bai, loai_noi_dung, thoi_luong_phut FROM bai_hoc ORDER BY ten_bai")
        finally:
            conn.close()
    return {
        "hoc_sinh": students,
        "mon_hoc": subjects,
        "de_thi": exams,
        "bai_hoc": lessons,
        "lop": [row["lop"] for row in classes],
    }


@app.get("/api/dashboard")
def api_dashboard():
    with oltp_lock:
        oltp = oltp_conn()
        try:
            with dw_lock:
                dw = dw_conn()
                try:
                    return dashboard(oltp, dw)
                finally:
                    dw.close()
        finally:
            oltp.close()


@app.get("/api/de-thi/{ma_de}/cau-hoi")
def questions(ma_de: str):
    with oltp_lock:
        conn = oltp_conn()
        try:
            exam = conn.execute("SELECT ma_de, ten_de, loai, so_cau, thoi_gian_phut FROM de_thi WHERE ma_de = ?", (ma_de,)).fetchone()
            if exam is None:
                raise HTTPException(404, "Không thấy đề thi")
            found = rows(
                conn,
                """
                SELECT ma_cau, noi_dung, phuong_an_a, phuong_an_b, phuong_an_c, phuong_an_d
                FROM cau_hoi WHERE ma_de = ? ORDER BY ma_cau
                """,
                (ma_de,),
            )
        finally:
            conn.close()
    return {"de": dict(exam), "cau_hoi": found}


@app.post("/api/hoc-tap/nop-bai")
def submit_exam(body: NopBai):
    with oltp_lock:
        conn = oltp_conn()
        try:
            student = conn.execute("SELECT ma_hs, ho_ten FROM hoc_sinh WHERE ma_hs = ?", (body.ma_hs,)).fetchone()
            if student is None:
                raise HTTPException(404, "Không thấy học sinh")
            bank = rows(conn, "SELECT * FROM cau_hoi WHERE ma_de = ? ORDER BY ma_cau", (body.ma_de,))
            if not bank:
                raise HTTPException(404, "Đề không có câu hỏi")
            result = grade(bank, body.answers, body.thoi_gian_giay)
            exam_id = insert_exam(
                conn,
                {
                    "ma_hs": body.ma_hs,
                    "ma_de": body.ma_de,
                    "nop_luc": now_str(),
                    "so_cau_dung": result["so_cau_dung"],
                    "so_cau_sai": result["so_cau_sai"],
                    "tong_so_cau": result["tong_so_cau"],
                    "diem": result["diem"],
                    "ty_le_dung": result["ty_le_dung"],
                    "thoi_gian_giay": result["thoi_gian_giay"],
                },
            )
            conn.commit()
        finally:
            conn.close()
    stats = run_batch("nop_bai")
    publish(
        {
            "type": "oltp",
            "nguon": "cong_hoc_tap",
            "su_kien": "nop_bai",
            "ma_hs": body.ma_hs,
            "ho_ten": student["ho_ten"],
            "diem": result["diem"],
            "luc": now_str(),
        }
    )
    return {"lan_lam_id": exam_id, "ket_qua": result, "etl": stats}


@app.post("/api/hoc-tap/phien")
def submit_session(body: PhienHoc):
    with oltp_lock:
        conn = oltp_conn()
        try:
            student = conn.execute("SELECT ma_hs, ho_ten FROM hoc_sinh WHERE ma_hs = ?", (body.ma_hs,)).fetchone()
            lesson = conn.execute("SELECT * FROM bai_hoc WHERE ma_bai = ?", (body.ma_bai,)).fetchone()
            if student is None or lesson is None:
                raise HTTPException(404, "Không thấy học sinh hoặc bài học")
            lesson = dict(lesson)
            ratio = body.thoi_luong_giay / max(lesson["thoi_luong_phut"] * 60, 1)
            video = 1 if lesson["loai_noi_dung"] == "VIDEO" and ratio >= 0.6 else 0
            score = diem_chuyen_can(body.thoi_luong_giay, body.so_tuong_tac, lesson["thoi_luong_phut"])
            cur = conn.execute(
                """
                INSERT INTO phien_hoc (
                    ma_hs, ma_bai, ket_thuc_luc, thoi_luong_giay, so_video,
                    so_tuong_tac, diem_chuyen_can, trang_thai
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'HOAN_THANH')
                """,
                (body.ma_hs, body.ma_bai, now_str(), body.thoi_luong_giay, video, body.so_tuong_tac, score),
            )
            session_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()
    stats = run_batch("phien_hoc")
    publish(
        {
            "type": "oltp",
            "nguon": "cong_hoc_tap",
            "su_kien": "phien_hoc",
            "ma_hs": body.ma_hs,
            "ho_ten": student["ho_ten"],
            "diem": score,
            "luc": now_str(),
        }
    )
    return {"phien_hoc_id": session_id, "diem_chuyen_can": score, "so_video": video, "etl": stats}


@app.get("/api/hoc-sinh/{ma_hs}/scd")
def scd(ma_hs: str):
    with dw_lock:
        dw = dw_conn()
        try:
            data = student_history(dw, ma_hs)
        finally:
            dw.close()
    if not data["phien_ban"]:
        raise HTTPException(404, "Chưa có phiên bản học sinh trong kho")
    return data


@app.post("/api/admin/hoc-vu")
def update_status(body: HocVu):
    if body.trang_thai not in STATUSES:
        raise HTTPException(400, "Trạng thái không hợp lệ")
    stamp = now_str()
    with oltp_lock:
        conn = oltp_conn()
        try:
            old = conn.execute("SELECT * FROM hoc_sinh WHERE ma_hs = ?", (body.ma_hs,)).fetchone()
            if old is None:
                raise HTTPException(404, "Không thấy học sinh")
            old = dict(old)
            if old["lop"] == body.lop and old["trang_thai_hoc_vu"] == body.trang_thai:
                raise HTTPException(400, "Lớp và trạng thái chưa đổi, SCD không sinh bản mới")
            reason = _reason(old, body.lop, body.trang_thai, body.ly_do)
            conn.execute(
                "UPDATE hoc_sinh SET lop = ?, trang_thai_hoc_vu = ? WHERE ma_hs = ?",
                (body.lop, body.trang_thai, body.ma_hs),
            )
            insert_event(
                conn,
                {
                    "ma_hs": body.ma_hs,
                    "thoi_diem": stamp,
                    "lop_moi": body.lop,
                    "trang_thai_moi": body.trang_thai,
                    "ly_do": reason,
                },
            )
            conn.commit()
        finally:
            conn.close()
    stats = run_batch("scd")
    publish({"type": "scd", "ma_hs": body.ma_hs, "lop": body.lop, "trang_thai": body.trang_thai, "ly_do": reason, "luc": stamp})
    with dw_lock:
        dw = dw_conn()
        try:
            history = student_history(dw, body.ma_hs)
        finally:
            dw.close()
    return {"etl": stats, "ly_do": reason, **history}


@app.post("/api/simulator/start")
def sim_start(body: SimConfig):
    return simulator.start(body.model_dump())


@app.post("/api/simulator/stop")
def sim_stop():
    return simulator.stop()


@app.get("/api/simulator/status")
def sim_status():
    return simulator.status()


@app.get("/api/stream/recent")
def recent():
    return {"su_kien": snapshot()}


@app.post("/api/demo/e2e")
def demo_e2e():
    stamp = now_str()
    with oltp_lock:
        conn = oltp_conn()
        try:
            before = conn.execute("SELECT COUNT(*) FROM lan_lam_bai").fetchone()[0]
            exam_id = insert_exam(
                conn,
                {
                    "ma_hs": "B23DCKD008",
                    "ma_de": "CSDL_L1",
                    "nop_luc": stamp,
                    "so_cau_dung": 4,
                    "so_cau_sai": 1,
                    "tong_so_cau": 5,
                    "diem": 8,
                    "ty_le_dung": 0.8,
                    "thoi_gian_giay": 640,
                },
            )
            conn.commit()
        finally:
            conn.close()
    stats = run_batch("e2e")
    with dw_lock:
        dw = dw_conn()
        try:
            fact = dw.execute(
                """
                SELECT f.diem_so, f.hoc_sinh_key, h.version_no, h.lop, h.ho_ten
                FROM fact_ket_qua_thi f
                JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
                WHERE f.lan_lam_id = ?
                """,
                (exam_id,),
            ).fetchone()
        finally:
            dw.close()
    publish({"type": "oltp", "nguon": "kich_ban", "su_kien": "e2e", "ma_hs": "B23DCKD008", "diem": 8, "luc": stamp})
    return {"truoc": before, "lan_lam_id": exam_id, "etl": stats, "fact": dict(fact) if fact else None}


@app.post("/api/demo/ban-ghi-ban")
def demo_bad():
    stamp = now_str()
    with oltp_lock:
        conn = oltp_conn()
        try:
            exam_id = insert_exam(
                conn,
                {
                    "ma_hs": "B23DCKD014",
                    "ma_de": "KDL_T1",
                    "nop_luc": stamp,
                    "so_cau_dung": 8,
                    "so_cau_sai": 1,
                    "tong_so_cau": 5,
                    "diem": 15,
                    "ty_le_dung": 0.2,
                    "thoi_gian_giay": -3,
                },
            )
            conn.commit()
        finally:
            conn.close()
    stats = run_batch("ban_ghi_ban")
    with dw_lock:
        dw = dw_conn()
        try:
            reject = dw.execute(
                "SELECT ly_do FROM etl_reject WHERE nguon = 'lan_lam_bai' AND nguon_id = ?",
                (exam_id,),
            ).fetchone()
            loaded = dw.execute("SELECT COUNT(*) FROM fact_ket_qua_thi WHERE lan_lam_id = ?", (exam_id,)).fetchone()[0]
        finally:
            dw.close()
    publish({"type": "oltp", "nguon": "kich_ban", "su_kien": "bai_ban", "ma_hs": "B23DCKD014", "diem": 15, "luc": stamp})
    return {"lan_lam_id": exam_id, "etl": stats, "ly_do": reject["ly_do"] if reject else "", "vao_fact": bool(loaded)}


@app.post("/api/reset")
def reset(body: ResetBody):
    if body.xac_nhan != "RESET":
        raise HTTPException(400, "Gõ RESET để làm lại dữ liệu")
    from mockup_generator.generate_sample_data import seed_if_empty

    simulator.stop()
    clear_hub()
    stop_etl()
    with oltp_lock:
        oltp = oltp_conn()
        try:
            wipe(oltp)
        finally:
            oltp.close()
    with dw_lock:
        dw = dw_conn()
        try:
            wipe(dw)
        finally:
            dw.close()
    init_schemas()
    seed_if_empty()
    stats = run_batch("reset")
    start_etl()
    return stats


@app.get("/api/chat-luong")
def quality():
    with dw_lock:
        dw = dw_conn()
        try:
            return quality_report(dw)
        finally:
            dw.close()


@app.get("/api/chat-luong/explain")
def explain():
    with dw_lock:
        dw = dw_conn()
        try:
            return explain_plans(dw)
        finally:
            dw.close()


@app.get("/api/chat-luong/bench")
def bench_api():
    with dw_lock:
        dw = dw_conn()
        try:
            return bench(dw)
        finally:
            dw.close()


@app.get("/api/olap/preset/{name}")
def olap_preset(name: str):
    with dw_lock:
        dw = dw_conn()
        try:
            try:
                return preset(dw, name)
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
        finally:
            dw.close()


@app.post("/api/olap/tuy-chinh")
def olap_custom(body: OlapBody):
    params = body.model_dump()
    with dw_lock:
        dw = dw_conn()
        try:
            try:
                if body.kieu == "pivot":
                    return query_pivot(dw, params)
                result = query_grouped(dw, params)
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
        finally:
            dw.close()
    result["thao_tac"] = body.thao_tac
    if body.thao_tac == "Roll-up":
        result["mo_ta"] = f"Roll-up đang đứng ở mức {body.muc}. Số dòng: {result['so_dong']}."
    elif body.thao_tac == "Drill-down":
        result["mo_ta"] = f"Drill-down đang đứng ở mức {body.muc}. Số dòng: {result['so_dong']}."
    elif body.thao_tac == "Slice":
        result["mo_ta"] = f"Slice giữ một giá trị môn = {body.ma_mon or 'tất cả'}. Số dòng: {result['so_dong']}."
    elif body.thao_tac == "Dice":
        result["mo_ta"] = "Dice áp cùng lúc các điều kiện đã chọn trên lớp, môn, loại và khoảng ngày."
    return result


@app.get("/api/olap/drill-across")
def olap_across(lop: str = "", ma_mon: str = "", limit: int = 12):
    with dw_lock:
        dw = dw_conn()
        try:
            return drill_across(dw, lop=lop, ma_mon=ma_mon, limit=max(0, min(limit, 500)))
        finally:
            dw.close()


@app.websocket("/ws/live")
async def live(socket: WebSocket):
    await socket.accept()
    clients.add(socket)
    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        clients.discard(socket)
    finally:
        clients.discard(socket)
