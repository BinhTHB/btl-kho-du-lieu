"""Kiểm tra luồng kho trên database riêng, không đụng dữ liệu demo."""

import os


def check(condition: bool, message: str) -> None:
    print(("  [OK] " if condition else "  [LOI] ") + message)
    if not condition:
        raise SystemExit(1)


def main() -> None:
    os.environ["LEARNDW_DB_SUFFIX"] = "_KiemTra"
    from app.database import drop_databases, dw_conn, init_schemas, now_str, oltp_conn, oltp_lock
    from app.etl import run_batch
    from app.ingest import insert_event, insert_exam
    from app.olap import drill_across, preset, quality_report
    from mockup_generator.generate_sample_data import seed_if_empty

    drop_databases()
    try:
        init_schemas()
        check(seed_if_empty(), "Sinh được nguồn OLTP")
        stats = run_batch("kiem_tra")
        check(stats["touched"], "Mẻ ETL đầu tiên có dữ liệu")
        check(
            stats["src_exam"] == stats["loaded_exam"] + stats["rejected_exam"],
            f"Đối soát bài thi {stats['src_exam']} = {stats['loaded_exam']} nạp + {stats['rejected_exam']} loại",
        )
        check(
            stats["src_session"] == stats["loaded_session"] + stats["rejected_session"],
            f"Đối soát phiên học {stats['src_session']} = {stats['loaded_session']} + {stats['rejected_session']}",
        )
        check(stats["loaded_exam"] > 0 and stats["loaded_session"] > 0, "Cả hai fact đều có dòng")

        dw = dw_conn()
        try:
            versions = [
                dict(row)
                for row in dw.execute(
                    """
                    SELECT version_no, lop, trang_thai_hoc_vu, start_date, end_date, is_current, hoc_sinh_key
                    FROM dim_hoc_sinh WHERE ma_hoc_sinh = 'B23DCKD004' ORDER BY version_no
                    """
                )
            ]
            check(len(versions) == 2, "Tường Anh có 2 phiên bản SCD")
            check(versions[0]["lop"] == "D23CQKD03" and versions[0]["is_current"] == 0, "Bản 1 là lớp cũ, đã đóng")
            check(versions[1]["lop"] == "D23CQCN01" and versions[1]["is_current"] == 1, "Bản 2 là lớp mới, đang hiệu lực")
            check(versions[0]["end_date"] == versions[1]["start_date"], "End_Date bản cũ khớp Start_Date bản mới")
            leaked = dw.execute(
                """
                SELECT COUNT(*) FROM fact_ket_qua_thi f
                JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
                JOIN dim_thoi_gian t ON t.date_key = f.date_key
                WHERE h.ma_hoc_sinh = 'B23DCKD004'
                  AND (
                    (t.ngay < '2026-10-12' AND h.version_no <> 1)
                    OR (t.ngay >= '2026-10-12' AND h.version_no <> 2)
                  )
                """
            ).fetchone()[0]
            check(leaked == 0, "Bài thi gắn đúng phiên bản học sinh tại thời điểm nộp")
            before = dw.execute(
                """
                SELECT COUNT(*) FROM fact_ket_qua_thi f
                JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
                JOIN dim_thoi_gian t ON t.date_key = f.date_key
                WHERE h.ma_hoc_sinh = 'B23DCKD004' AND t.ngay < '2026-10-12'
                """
            ).fetchone()[0]
            after = dw.execute(
                """
                SELECT COUNT(*) FROM fact_ket_qua_thi f
                JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
                JOIN dim_thoi_gian t ON t.date_key = f.date_key
                WHERE h.ma_hoc_sinh = 'B23DCKD004' AND t.ngay >= '2026-10-12'
                """
            ).fetchone()[0]
            check(before > 0 and after > 0, "Có bài cả trước và sau ngày chuyển lớp")

            report = quality_report(dw)
            check(report["khop_bai"] and report["khop_phien"] and report["khop_summary"], "Audit, fact và summary khớp số dòng")

            across = drill_across(dw)
            check(across["chi_co_chuyen_can"] > 0, "Drill-across giữ học sinh chỉ có chuyên cần")
            check(across["chi_co_diem"] > 0, "Drill-across giữ học sinh chỉ có điểm")
            sample = across["vi_du_nhan_ban"]
            check(sample is not None, "Có cặp học sinh-môn để minh họa nhân bản")
            check(
                sample["so_dong_khi_join_thang"] == sample["so_luot_thi"] * sample["so_phien"],
                "JOIN thẳng hai fact sinh đúng tích số dòng",
            )
            check(sample["tong_diem_bi_nhan"] != sample["tong_diem_dung"], "Tổng điểm bị nhân khi join thẳng")

            rolled = preset(dw, "roll-up")
            drilled = preset(dw, "drill-down")
            sliced = preset(dw, "slice")
            diced = preset(dw, "dice")
            pivoted = preset(dw, "pivot")
            check(rolled["so_dong"] < drilled["so_dong"], "Roll-up ít dòng hơn drill-down")
            check(sliced["so_dong"] > 0, "Slice môn Kho dữ liệu có số liệu")
            check(diced["so_dong"] > 0, "Dice lớp, môn và khoảng ngày có số liệu")
            width = {len(row) for row in pivoted["matran"]}
            check(pivoted["hang"] and pivoted["cot"] and width == {len(pivoted["cot"])}, "Pivot là ma trận chữ nhật")
        finally:
            dw.close()

        with oltp_lock:
            oltp = oltp_conn()
            try:
                bad_id = insert_exam(
                    oltp,
                    {
                        "ma_hs": "B23DCKD008",
                        "ma_de": "CSDL_L1",
                        "nop_luc": now_str(),
                        "so_cau_dung": 9,
                        "so_cau_sai": 1,
                        "tong_so_cau": 5,
                        "diem": 15,
                        "ty_le_dung": 0.1,
                        "thoi_gian_giay": -5,
                    },
                )
                unknown_id = insert_exam(
                    oltp,
                    {
                        "ma_hs": "NGOAI_DS",
                        "ma_de": "KDL_L1",
                        "nop_luc": now_str(),
                        "so_cau_dung": 4,
                        "so_cau_sai": 1,
                        "tong_so_cau": 5,
                        "diem": 8,
                        "ty_le_dung": 0.8,
                        "thoi_gian_giay": 400,
                    },
                )
                good_id = insert_exam(
                    oltp,
                    {
                        "ma_hs": "B23DCKD008",
                        "ma_de": "CSDL_L1",
                        "nop_luc": now_str(),
                        "so_cau_dung": 5,
                        "so_cau_sai": 0,
                        "tong_so_cau": 5,
                        "diem": 10,
                        "ty_le_dung": 1,
                        "thoi_gian_giay": 500,
                    },
                )
                insert_event(
                    oltp,
                    {
                        "ma_hs": "B23DCKD004",
                        "thoi_diem": now_str(),
                        "lop_moi": "D23CQCN01",
                        "trang_thai_moi": "CANH_BAO_HOC_VU",
                        "ly_do": "CANH_BAO_HOC_VU",
                    },
                )
                oltp.execute(
                    "UPDATE hoc_sinh SET trang_thai_hoc_vu = 'CANH_BAO_HOC_VU' WHERE ma_hs = 'B23DCKD004'"
                )
                oltp.commit()
            finally:
                oltp.close()

        again = run_batch("kiem_tra_2")
        check(again["rejected_exam"] == 1, "Cổng chất lượng loại đúng một bài bẩn")
        check(again["unknown_exam"] == 1, "Mã lạ vẫn được nạp bằng unknown member")
        check(again["loaded_exam"] == 2, "Bài hợp lệ và bài mã lạ đều vào fact")
        check(again["scd_new"] == 1, "Cảnh báo học vụ sinh thêm một phiên bản")

        dw = dw_conn()
        try:
            bad_in_fact = dw.execute(
                "SELECT COUNT(*) FROM fact_ket_qua_thi WHERE lan_lam_id = ?",
                (bad_id,),
            ).fetchone()[0]
            unknown_key = dw.execute(
                "SELECT hoc_sinh_key FROM fact_ket_qua_thi WHERE lan_lam_id = ?",
                (unknown_id,),
            ).fetchone()[0]
            good_key = dw.execute(
                "SELECT hoc_sinh_key FROM fact_ket_qua_thi WHERE lan_lam_id = ?",
                (good_id,),
            ).fetchone()[0]
            current = dw.execute(
                """
                SELECT version_no, trang_thai_hoc_vu, is_current
                FROM dim_hoc_sinh WHERE ma_hoc_sinh = 'B23DCKD004' AND is_current = 1
                """
            ).fetchone()
            old_kept = dw.execute(
                """
                SELECT COUNT(*) FROM fact_ket_qua_thi f
                JOIN dim_hoc_sinh h ON h.hoc_sinh_key = f.hoc_sinh_key
                WHERE h.ma_hoc_sinh = 'B23DCKD004' AND h.version_no = 1
                """
            ).fetchone()[0]
            check(bad_in_fact == 0, "Bài bẩn không có trong fact")
            check(unknown_key == -1, "Bài mã lạ trỏ về khóa -1")
            check(current["version_no"] == 3 and current["trang_thai_hoc_vu"] == "CANH_BAO_HOC_VU", "Bản hiện tại là cảnh báo học vụ")
            check(good_key != -1, "Bài mới của Bình vẫn gắn được học sinh")
            check(old_kept == before, "Fact cũ không bị đổi sang phiên bản mới")
            report = quality_report(dw)
            check(report["khop_bai"] and report["khop_summary"], "Sau mẻ thứ hai số dòng vẫn khớp")
        finally:
            dw.close()
        print("Self-check xong.")
    finally:
        drop_databases()


if __name__ == "__main__":
    main()
