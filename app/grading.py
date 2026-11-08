def grade(questions, answers, thoi_gian_giay: int) -> dict:
    dung = 0
    chi_tiet = []
    for question in questions:
        chosen = str(answers.get(str(question["ma_cau"]), answers.get(question["ma_cau"], ""))).strip().upper()
        correct = chosen == question["dap_an_dung"]
        dung += int(correct)
        chi_tiet.append(
            {
                "ma_cau": question["ma_cau"],
                "noi_dung": question["noi_dung"],
                "chon": chosen,
                "dung": correct,
                "dap_an": question["dap_an_dung"],
            }
        )
    total = len(questions)
    sai = total - dung
    diem = round(10 * dung / total, 2) if total else 0
    ty_le = round(dung / total, 4) if total else 0
    return {
        "so_cau_dung": dung,
        "so_cau_sai": sai,
        "tong_so_cau": total,
        "diem": diem,
        "ty_le_dung": ty_le,
        "thoi_gian_giay": thoi_gian_giay,
        "chi_tiet": chi_tiet,
    }


def diem_chuyen_can(thoi_luong_giay: int, so_tuong_tac: int, chuan_phut: int) -> float:
    phut = thoi_luong_giay / 60
    ty_le_xem = min(1.0, phut / max(chuan_phut, 1))
    diem = 7 * ty_le_xem + min(max(so_tuong_tac, 0), 10) * 0.3
    return round(min(10.0, max(0.0, diem)), 2)
