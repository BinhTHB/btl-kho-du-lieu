const TT = {
  DANG_HOC: "Đang học",
  BAO_LUU: "Bảo lưu",
  CANH_BAO_HOC_VU: "Cảnh báo học vụ",
  KHONG_XAC_DINH: "Không xác định",
};
const state = { meta: null, muc: "thang", questions: [], started: 0, tuongTac: 1 };

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

function num(value) {
  if (value === null || value === undefined || value === "") return "–";
  const n = Number(value);
  if (Number.isNaN(n)) return esc(value);
  return n.toLocaleString("vi-VN", { maximumFractionDigits: 2 }).replace(/\.(?=\d{3}(\D|$))/g, " ");
}

function cell(value, header) {
  if (value === null || value === undefined || value === "") return "–";
  if (typeof value === "number" && String(header).includes("Tỷ lệ")) return `${(value * 100).toFixed(1)}%`;
  if (typeof value === "number") return num(value);
  if (header === "Is_Current" || header === "Hiệu lực") return value ? "1" : "0";
  if (TT[value]) return esc(TT[value]);
  return esc(value);
}

function toast(message, ok = true) {
  const el = $("#toast");
  el.textContent = message;
  el.className = ok ? "show" : "show bad";
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.className = ""; }, 3600);
}

async function api(path, options) {
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || res.statusText);
  return data;
}

function table(columns, rows, rowClass) {
  if (!rows.length) return "<p class='hint'>Chưa có dòng nào.</p>";
  const head = columns.map((col) => `<th>${esc(col)}</th>`).join("");
  const body = rows.map((row, index) => {
    const cls = rowClass ? rowClass(row, index) : "";
    const tds = row.map((value, i) => `<td>${cell(value, columns[i])}</td>`).join("");
    return `<tr class="${cls}">${tds}</tr>`;
  }).join("");
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function bars(el, rows, labelKey, valueKey) {
  const max = Math.max(...rows.map((row) => Number(row[valueKey]) || 0), 1);
  el.innerHTML = rows.map((row) => `
    <div class="bar-row">
      <span>${esc(row[labelKey])}</span>
      <div class="track"><div style="width:${(Number(row[valueKey]) || 0) / max * 100}%"></div></div>
      <b>${num(row[valueKey])}</b>
    </div>
  `).join("") || "<p class='hint'>Chưa có số liệu.</p>";
}

function renderDashboard(data) {
  const p = data.pipeline;
  const k = data.kpi;
  $("#pipe").innerHTML = [
    ["OLTP bài / phiên", `${num(p.oltp_bai)} / ${num(p.oltp_phien)}`],
    ["Bị loại", num(p.bi_loai)],
    ["Fact bài / phiên", `${num(p.fact_bai)} / ${num(p.fact_phien)}`],
    ["Dòng summary", num(p.dong_summary)],
    ["Mã lạ giữ lại", num(k.unknown_member)],
  ].map(([name, value]) => `<li><b>${name}</b><strong>${value}</strong></li>`).join("");
  const cards = [
    ["Điểm trung bình", k.diem_tb],
    ["Tổng phút học", k.tong_phut],
    ["Phiên bản SCD", k.phien_ban_scd],
    ["Học sinh hiện tại", k.hoc_sinh_hien_tai],
  ];
  $("#kpis").innerHTML = cards.map(([name, value]) => `<div class="kpi"><span>${name}</span><b>${num(value)}</b></div>`).join("");
  bars($("#bars-mon"), data.theo_mon, "ten_mon", "diem_tb");
  bars($("#bars-ngay"), data.theo_ngay, "ngay", "so_luot");
}

function fillSelect(el, items, valueKey, labelFn, first) {
  const current = el.value;
  el.innerHTML = (first ? `<option value="">${esc(first)}</option>` : "") + items.map((item) => {
    const value = item[valueKey];
    return `<option value="${esc(value)}">${esc(labelFn(item))}</option>`;
  }).join("");
  if ([...el.options].some((opt) => opt.value === current)) el.value = current;
}

function bindMeta(meta) {
  state.meta = meta;
  const labelHs = (row) => `${row.ho_ten} · ${row.ma_hs} · ${row.lop}`;
  fillSelect($("#hs-select"), meta.hoc_sinh, "ma_hs", labelHs);
  fillSelect($("#scd-hs"), meta.hoc_sinh, "ma_hs", labelHs);
  fillSelect($("#de-select"), meta.de_thi, "ma_de", (row) => `${row.ten_de} (${row.loai})`);
  fillSelect($("#bai-select"), meta.bai_hoc, "ma_bai", (row) => `${row.ten_bai} · ${row.thoi_luong_phut} phút`);
  fillSelect($("#f-mon"), meta.mon_hoc, "ma_mon", (row) => row.ten_mon, "Mọi môn");
  fillSelect($("#ax-mon"), meta.mon_hoc, "ma_mon", (row) => row.ten_mon, "Mọi môn");
  const lops = meta.lop.map((lop) => ({ lop }));
  fillSelect($("#f-lop"), lops, "lop", (row) => row.lop, "Mọi lớp");
  fillSelect($("#ax-lop"), lops, "lop", (row) => row.lop, "Mọi lớp hiện tại");
  fillSelect($("#scd-lop"), lops, "lop", (row) => row.lop);
  const members = meta.hoc_sinh.filter((row) => row.vai_tro === "thanh_vien");
  $("#member-chips").innerHTML = members.map((row) => `<button type="button" class="ghost" data-hs="${esc(row.ma_hs)}">${esc(row.ho_ten)}</button>`).join("");
  if ([...$("#hs-select").options].some((opt) => opt.value === "B23DCKD004")) {
    $("#hs-select").value = "B23DCKD004";
    $("#scd-hs").value = "B23DCKD004";
  }
  $("#scd-quick").innerHTML = [
    ["B23DCKD004", "D23CQKD03", "DANG_HOC", "Kịch bản chuyển lớp"],
    ["B23DCKD004", "D23CQCN01", "CANH_BAO_HOC_VU", "Kịch bản cảnh báo học vụ"],
    ["HS-BL01", "D23CQKD03", "DANG_HOC", "Kịch bản hết bảo lưu"],
    ["B23DCKD008", "D23CQVT04", "DANG_HOC", "Kịch bản chuyển lớp thứ hai"],
  ].map(([ma, lop, tt, label]) => `<button type="button" class="ghost" data-quick="${ma}|${lop}|${tt}">${label}</button>`).join("");
}

function renderOlap(data) {
  $("#olap-title").textContent = data.thao_tac || "Kết quả";
  $("#olap-note").textContent = data.mo_ta || "";
  $("#olap-sql").textContent = data.sql || "";
  if (data.kieu === "pivot") {
    const head = ["<th></th>", ...data.cot.map((col) => `<th>${esc(col)}</th>`)].join("");
    const body = data.hang.map((hang, i) => {
      const cells = data.matran[i].map((value) => `<td>${value === null ? "–" : num(value)}</td>`).join("");
      return `<tr><th>${esc(hang)}</th>${cells}</tr>`;
    }).join("");
    $("#olap-result").innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
    return;
  }
  $("#olap-result").innerHTML = table(data.cot, data.dong);
}

function renderFanout(sample, summary) {
  if (!sample) {
    $("#fanout").textContent = "Chưa có học sinh nào vừa có nhiều bài thi vừa có nhiều phiên học trên cùng một môn.";
    return;
  }
  $("#fanout").innerHTML = `
    <strong>${esc(sample.ma_hoc_sinh)} · ${esc(sample.ma_mon)}</strong>:
    ${sample.so_luot_thi} bài và ${sample.so_phien} phiên.
    Tổng điểm đúng ${num(sample.tong_diem_dung)}, tổng phút đúng ${num(sample.tong_phut_dung)}.
    Nếu JOIN thẳng hai fact thì thành ${num(sample.so_dong_khi_join_thang)} dòng,
    tổng điểm bị kéo thành ${num(sample.tong_diem_bi_nhan)}, tổng phút thành ${num(sample.tong_phut_bi_nhan)}.
    Toàn bộ drill-across: ${summary.chi_co_diem} cặp chỉ có điểm, ${summary.chi_co_chuyen_can} cặp chỉ có chuyên cần, ${summary.ca_hai} cặp có cả hai.
    Đang hiện ${summary.so_dong_hien}/${summary.so_dong} dòng.
  `;
}

async function loadDashboard() {
  renderDashboard(await api("/api/dashboard"));
}

async function loadQuiz() {
  const data = await api(`/api/de-thi/${$("#de-select").value}/cau-hoi`);
  state.questions = data.cau_hoi;
  state.started = Date.now();
  $("#quiz").innerHTML = data.cau_hoi.map((q, index) => `
    <div class="quiz-q">
      <p><b>Câu ${index + 1}.</b> ${esc(q.noi_dung)}</p>
      ${["a", "b", "c", "d"].map((key) => `
        <label class="choice"><input type="radio" name="q${q.ma_cau}" value="${key.toUpperCase()}"> ${key.toUpperCase()}. ${esc(q[`phuong_an_${key}`])}</label>
      `).join("")}
    </div>
  `).join("") + `<button id="btn-nop">Nộp bài</button><div id="quiz-result"></div>`;
}

function renderLesson() {
  const bai = state.meta.bai_hoc.find((row) => row.ma_bai === $("#bai-select").value);
  if (!bai) return;
  state.tuongTac = 1;
  $("#lesson").innerHTML = `
    <p>${esc(bai.ten_bai)} · ${esc(bai.loai_noi_dung)} · chuẩn ${bai.thoi_luong_phut} phút.</p>
    <label>Số phút ghi nhận <input id="lesson-min" type="number" min="1" max="${bai.thoi_luong_phut}" value="${Math.max(1, Math.round(bai.thoi_luong_phut * 0.8))}"></label>
    <p>Số lần bấm tương tác: <b id="tap-count">1</b></p>
    <div class="chips">
      <button type="button" id="btn-tap" class="ghost">Thêm một tương tác</button>
      <button type="button" id="btn-phien">Ghi phiên vào OLTP</button>
    </div>
    <p id="lesson-result" class="hint"></p>
  `;
}

async function loadScd() {
  const ma = $("#scd-hs").value;
  const student = state.meta.hoc_sinh.find((row) => row.ma_hs === ma);
  if (student) {
    $("#scd-lop").value = student.lop;
    $("#scd-tt").value = student.trang_thai_hoc_vu;
  }
  const data = await api(`/api/hoc-sinh/${ma}/scd`);
  $("#scd-table").innerHTML = table(
    ["Ver", "Lớp", "Trạng thái", "Lý do", "Start_Date", "End_Date", "Is_Current", "Khóa"],
    data.phien_ban.map((row) => [row.version_no, row.lop, row.trang_thai_hoc_vu, row.ly_do, row.start_date, row.end_date, row.is_current, row.hoc_sinh_key]),
    (row) => (row[6] ? "current" : ""),
  );
  $("#scd-facts").innerHTML = table(
    ["Ngày", "Đề", "Điểm", "Khóa HS", "Ver", "Lớp tại lúc thi", "Trạng thái lúc thi"],
    data.bai_gan_day.map((row) => [row.ngay, row.ten_de, row.diem_so, row.hoc_sinh_key, row.version_no, row.lop, row.trang_thai_hoc_vu]),
  );
}

function pushLog(event) {
  const li = document.createElement("li");
  li.className = event.type || "";
  const when = event.luc ? event.luc.slice(11, 19) : new Date().toLocaleTimeString("vi-VN");
  if (event.type === "etl") {
    li.textContent = `${when}  ETL #${event.batch_id}: bài ${event.loaded_exam}/${event.src_exam}, phiên ${event.loaded_session}/${event.src_session}, loại ${event.rejected_exam + event.rejected_session}, SCD mới ${event.scd_new}, ${event.duration_ms} ms`;
  } else if (event.type === "oltp") {
    li.textContent = `${when}  OLTP ${event.su_kien} · ${event.ma_hs} · ${event.diem ?? ""}`;
  } else if (event.type === "scd") {
    li.textContent = `${when}  SCD ${event.ma_hs} → ${event.lop} / ${event.trang_thai}`;
  } else if (event.type === "error") {
    li.textContent = event.message;
  } else {
    li.textContent = `${when}  ${event.su_kien || event.type}`;
  }
  const log = $("#log");
  log.prepend(li);
  while (log.children.length > 50) log.lastChild.remove();
}

async function loadQuality() {
  const data = await api("/api/chat-luong");
  const cards = [
    ["Nguồn bài", data.tong.src_exam],
    ["Nạp fact bài", data.tong.loaded_exam],
    ["Loại bài", data.tong.rejected_exam],
    ["Summary khớp", data.khop_summary ? "Có" : "Không"],
  ];
  $("#q-kpis").innerHTML = cards.map(([name, value]) => `<div class="kpi"><span>${name}</span><b>${typeof value === "number" ? num(value) : value}</b></div>`).join("");
  $("#q-batch").innerHTML = table(
    ["Mẻ", "Nguồn gọi", "Bài nguồn", "Nạp", "Loại", "Phiên nạp", "SCD mới", "ms", "TT"],
    data.me.map((row) => [row.batch_id, row.trigger_name, row.src_exam, row.loaded_exam, row.rejected_exam, row.loaded_session, row.scd_new, row.duration_ms, row.status]),
  );
  $("#q-reject").innerHTML = table(
    ["ID", "Nguồn", "Mã nguồn", "Lý do", "Lúc"],
    data.loai.map((row) => [row.id, row.nguon, row.nguon_id, row.ly_do, row.created_at]),
  );
  const plan = await api("/api/chat-luong/explain");
  $("#q-plan").textContent = Object.entries(plan).map(([name, item]) => `${name}\n${item.sql}\n${item.ke_hoach.join("\n")}`).join("\n\n");
}

function filters() {
  return {
    nguon: $("#f-nguon").value,
    muc: $("#f-muc").value,
    ma_mon: $("#f-mon").value,
    lop: $("#f-lop").value,
    tu_ngay: $("#f-tu").value,
    den_ngay: $("#f-den").value,
  };
}

function shiftMuc(step) {
  const levels = ["ngay", "tuan", "thang", "hoc_ky", "nam"];
  const index = Math.min(levels.length - 1, Math.max(0, levels.indexOf($("#f-muc").value) + step));
  $("#f-muc").value = levels[index];
  return levels[index];
}

function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${proto}://${location.host}/ws/live`);
  socket.onopen = () => {
    $("#ws-dot").classList.add("on");
    $("#ws-text").textContent = "Đang nghe dòng";
    socket.send("ping");
  };
  socket.onmessage = (message) => {
    const event = JSON.parse(message.data);
    pushLog(event);
    if (event.type === "etl" && $("#page-dash").classList.contains("active")) loadDashboard().catch(() => {});
    if (event.type === "etl" && $("#page-chat").classList.contains("active")) loadQuality().catch(() => {});
  };
  socket.onclose = () => {
    $("#ws-dot").classList.remove("on");
    $("#ws-text").textContent = "Mất nối, đang thử lại";
    setTimeout(connect, 1500);
  };
}

function show(page) {
  $$(".page").forEach((el) => el.classList.remove("active"));
  $(`#page-${page}`).classList.add("active");
  $$("nav button").forEach((btn) => btn.classList.toggle("active", btn.dataset.page === page));
  if (page === "dash") loadDashboard().catch((err) => toast(err.message, false));
  if (page === "scd") loadScd().catch((err) => toast(err.message, false));
  if (page === "chat") loadQuality().catch((err) => toast(err.message, false));
  if (page === "hoc") renderLesson();
}

document.addEventListener("click", async (event) => {
  const pageBtn = event.target.closest("nav button");
  if (pageBtn) show(pageBtn.dataset.page);
  const member = event.target.closest("[data-hs]");
  if (member) {
    $("#hs-select").value = member.dataset.hs;
    toast(`Đang thao tác với ${member.textContent.trim()}`);
  }
  const quick = event.target.closest("[data-quick]");
  if (quick) {
    const [ma, lop, tt] = quick.dataset.quick.split("|");
    $("#scd-hs").value = ma;
    $("#scd-lop").value = lop;
    $("#scd-tt").value = tt;
    $("#btn-scd").click();
  }
  const presetBtn = event.target.closest("[data-preset]");
  if (presetBtn) {
    try {
      renderOlap(await api(`/api/olap/preset/${presetBtn.dataset.preset}`));
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "btn-refresh") loadDashboard().catch((err) => toast(err.message, false));
  if (event.target.id === "btn-nop") {
    const answers = {};
    state.questions.forEach((q) => {
      const chosen = document.querySelector(`input[name="q${q.ma_cau}"]:checked`);
      if (chosen) answers[q.ma_cau] = chosen.value;
    });
    const seconds = Math.max(1, Math.round((Date.now() - state.started) / 1000));
    try {
      const data = await api("/api/hoc-tap/nop-bai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ma_hs: $("#hs-select").value, ma_de: $("#de-select").value, answers, thoi_gian_giay: seconds }),
      });
      const lines = data.ket_qua.chi_tiet.map((row) => `${row.dung ? "Đúng" : "Sai"} · chọn ${row.chon || "trống"} · đáp án ${row.dap_an}`).join("<br>");
      $("#quiz-result").innerHTML = `<p><b>Điểm ${num(data.ket_qua.diem)}</b> · đúng ${data.ket_qua.so_cau_dung}/${data.ket_qua.tong_so_cau}. ETL nạp ${data.etl.loaded_exam || 0} bài.</p>${lines}`;
      toast(`Đã nộp, điểm ${data.ket_qua.diem}`);
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "btn-tap") {
    state.tuongTac += 1;
    $("#tap-count").textContent = state.tuongTac;
  }
  if (event.target.id === "btn-phien") {
    const minutes = Number($("#lesson-min").value || 1);
    try {
      const data = await api("/api/hoc-tap/phien", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ma_hs: $("#hs-select").value,
          ma_bai: $("#bai-select").value,
          thoi_luong_giay: Math.max(60, minutes * 60),
          so_tuong_tac: state.tuongTac,
        }),
      });
      $("#lesson-result").textContent = `Đã ghi phiên. Điểm chuyên cần ${data.diem_chuyen_can}, video tính ${data.so_video}.`;
      toast("Phiên học đã vào kho");
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "btn-scd") {
    try {
      const data = await api("/api/admin/hoc-vu", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ma_hs: $("#scd-hs").value, lop: $("#scd-lop").value, trang_thai: $("#scd-tt").value }),
      });
      const student = state.meta.hoc_sinh.find((row) => row.ma_hs === $("#scd-hs").value);
      if (student) {
        student.lop = $("#scd-lop").value;
        student.trang_thai_hoc_vu = $("#scd-tt").value;
      }
      toast(`SCD lý do ${data.ly_do}, bản mới đã mở`);
      await loadScd();
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "sim-start") {
    try {
      const data = await api("/api/simulator/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          students_per_tick: Number($("#sim-n").value),
          interval_ms: Number($("#sim-ms").value),
          include_bad: $("#sim-bad").checked,
          include_members: $("#sim-mem").checked,
        }),
      });
      toast("Bộ sinh đang chạy");
      $("#sim-kpis").innerHTML = `<div class="kpi"><span>Trạng thái</span><b>${data.running ? "Đang chảy" : "Dừng"}</b></div>`;
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "sim-stop") {
    const data = await api("/api/simulator/stop", { method: "POST" });
    toast(data.running ? "Vẫn chạy" : "Đã dừng bộ sinh", !data.running);
  }
  if (event.target.id === "btn-e2e") {
    try {
      const data = await api("/api/demo/e2e", { method: "POST" });
      $("#demo-note").textContent = data.fact
        ? `OLTP tăng sau mốc ${data.truoc}. Fact điểm ${data.fact.diem_so}, khóa học sinh ${data.fact.hoc_sinh_key}, phiên bản ${data.fact.version_no}, lớp ${data.fact.lop}.`
        : "Không thấy fact tương ứng.";
      toast("Kịch bản end-to-end xong");
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "btn-bad") {
    try {
      const data = await api("/api/demo/ban-ghi-ban", { method: "POST" });
      $("#demo-note").textContent = `Bài ${data.lan_lam_id} không vào fact (${data.vao_fact ? "có" : "không"}). Lý do: ${data.ly_do}`;
      toast("Bản ghi bẩn đã bị chặn");
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "btn-rollup" || event.target.id === "btn-drill" || event.target.id === "btn-slice" || event.target.id === "btn-dice" || event.target.id === "btn-pivot" || event.target.id === "btn-swap") {
    try {
      if (event.target.id === "btn-rollup") shiftMuc(1);
      if (event.target.id === "btn-drill") shiftMuc(-1);
      if (event.target.id === "btn-swap") {
        const hang = $("#p-hang").value;
        $("#p-hang").value = $("#p-cot").value;
        $("#p-cot").value = hang;
      }
      let thao = "Tuy chinh";
      if (event.target.id === "btn-rollup") thao = "Roll-up";
      if (event.target.id === "btn-drill") thao = "Drill-down";
      if (event.target.id === "btn-slice") thao = "Slice";
      if (event.target.id === "btn-dice") thao = "Dice";
      if (event.target.id === "btn-pivot" || event.target.id === "btn-swap") thao = "Pivot";
      const body = { ...filters(), thao_tac: thao, kieu: thao === "Pivot" ? "pivot" : "bang", hang: $("#p-hang").value, cot: $("#p-cot").value };
      if (thao === "Slice") {
        body.lop = "";
        body.tu_ngay = "";
        body.den_ngay = "";
        if (!body.ma_mon) body.ma_mon = "KDL";
      }
      if (thao === "Dice") {
        const used = [body.ma_mon, body.lop, body.tu_ngay && body.den_ngay].filter(Boolean).length;
        if (used < 2) {
          toast("Dice cần ít nhất hai điều kiện, ví dụ môn và lớp.", false);
          return;
        }
      }
      renderOlap(await api("/api/olap/tuy-chinh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }));
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "btn-across") {
    try {
      const data = await api(`/api/olap/drill-across?lop=${encodeURIComponent($("#ax-lop").value)}&ma_mon=${encodeURIComponent($("#ax-mon").value)}`);
      $("#across-table").innerHTML = table(data.cot, data.dong);
      $("#across-note").textContent = data.mo_ta;
      renderFanout(data.vi_du_nhan_ban, data);
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "btn-reset") {
    const word = window.prompt("Gõ RESET để xóa và sinh lại dữ liệu mẫu");
    if (word !== "RESET") return;
    try {
      toast("Đang làm lại dữ liệu...");
      await api("/api/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ xac_nhan: "RESET" }),
      });
      bindMeta(await api("/api/meta"));
      await loadDashboard();
      toast("Đã sinh lại nguồn và nạp kho");
    } catch (err) {
      toast(err.message, false);
    }
  }
  if (event.target.id === "btn-bench") {
    try {
      const data = await api("/api/chat-luong/bench");
      $("#bench-note").textContent = `${data.so_vong} vòng: summary ${data.summary_ms} ms trên ${data.dong_summary} dòng tổng hợp; quét fact ${data.atomic_ms} ms trên ${data.dong_fact} dòng. Với vài trăm dòng, chênh lệch còn nhỏ. Summary có ích khi fact dày lên vì đã gom sẵn.`;
    } catch (err) {
      toast(err.message, false);
    }
  }
});

$("#de-select").addEventListener("change", () => loadQuiz().catch((err) => toast(err.message, false)));
$("#bai-select").addEventListener("change", renderLesson);
$("#hs-select").addEventListener("change", () => { $("#scd-hs").value = $("#hs-select").value; });
$("#scd-hs").addEventListener("change", () => loadScd().catch((err) => toast(err.message, false)));

async function boot() {
  try {
    bindMeta(await api("/api/meta"));
    await loadQuiz();
    renderLesson();
    await loadDashboard();
    const recent = await api("/api/stream/recent");
    recent.su_kien.forEach(pushLog);
    connect();
  } catch (err) {
    toast(err.message, false);
  }
}

boot();
