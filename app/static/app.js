const TT = {
  DANG_HOC: "Đang học",
  BAO_LUU: "Bảo lưu",
  CANH_BAO_HOC_VU: "Cảnh báo học vụ",
  KHONG_XAC_DINH: "Không xác định",
};

const state = {
  meta: null,
  questions: [],
  started: 0,
  tuongTac: 1,
};

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
  if (header === "Is_Current" || header === "Hiệu lực") return value ? "1 (Hiện thời)" : "0 (Lịch sử)";
  if (TT[value]) return esc(TT[value]);
  return esc(value);
}

function toast(message, ok = true) {
  const el = $("#toast");
  if (!el) return;
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
  if (!rows || !rows.length) return "<p class='empty-state'>Không có dữ liệu phù hợp.</p>";
  const head = columns.map((col) => `<th>${esc(col)}</th>`).join("");
  const body = rows.map((row, index) => {
    const cls = rowClass ? rowClass(row, index) : "";
    const tds = row.map((value, i) => `<td>${cell(value, columns[i])}</td>`).join("");
    return `<tr class="${cls}">${tds}</tr>`;
  }).join("");
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function bars(el, rows, labelKey, valueKey) {
  if (!el) return;
  const safeRows = rows || [];
  const max = Math.max(...safeRows.map((row) => Number(row[valueKey]) || 0), 1);
  el.innerHTML = safeRows.map((row) => `
    <div class="bar-row">
      <span class="bar-label" title="${esc(row[labelKey])}">${esc(row[labelKey])}</span>
      <div class="bar-track">
        <div class="bar-fill" style="width:${(Number(row[valueKey]) || 0) / max * 100}%"></div>
      </div>
      <b class="bar-val">${num(row[valueKey])}</b>
    </div>
  `).join("") || "<p class='empty-state'>Chưa có số liệu thống kê.</p>";
}

function fillSelect(el, items, valueKey, labelFn, first) {
  if (!el) return;
  const current = el.value;
  el.innerHTML = (first ? `<option value="">${esc(first)}</option>` : "") + (items || []).map((item) => {
    const value = item[valueKey];
    return `<option value="${esc(value)}">${esc(labelFn(item))}</option>`;
  }).join("");
  if ([...el.options].some((opt) => opt.value === current)) el.value = current;
}

function updateExamSummary() {
  const deSel = $("#de-select");
  const summaryEl = $("#exam-summary");
  if (!deSel || !summaryEl || !state.meta) return;
  const exam = (state.meta.de_thi || []).find((e) => e.ma_de === deSel.value);
  if (!exam) {
    summaryEl.innerHTML = "";
    return;
  }
  summaryEl.innerHTML = `
    <strong>Hình thức:</strong> ${esc(exam.loai)} &nbsp;|&nbsp;
    <strong>Độ khó:</strong> ${esc(exam.do_kho)} &nbsp;|&nbsp;
    <strong>Quy mô:</strong> ${exam.so_cau} câu &nbsp;|&nbsp;
    <strong>Thời gian:</strong> ${exam.thoi_gian_phut} phút
  `;
}

function bindMeta(meta) {
  state.meta = meta;
  const labelHs = (row) => `${row.ma_hs} – ${row.ho_ten} (${row.lop})`;
  
  fillSelect($("#hs-select"), meta.hoc_sinh, "ma_hs", labelHs);
  fillSelect($("#scd-hs"), meta.hoc_sinh, "ma_hs", labelHs);
  fillSelect($("#de-select"), meta.de_thi, "ma_de", (row) => `${row.ten_de} [${row.ma_de}]`);
  fillSelect($("#bai-select"), meta.bai_hoc, "ma_bai", (row) => `${row.ten_bai} (${row.thoi_luong_phut} phút)`);
  fillSelect($("#f-mon"), meta.mon_hoc, "ma_mon", (row) => row.ten_mon, "Mọi môn học");
  fillSelect($("#ax-mon"), meta.mon_hoc, "ma_mon", (row) => row.ten_mon, "Mọi môn học");

  const lops = (meta.lop || []).map((lop) => ({ lop }));
  fillSelect($("#f-lop"), lops, "lop", (row) => row.lop, "Mọi lớp");
  fillSelect($("#ax-lop"), lops, "lop", (row) => row.lop, "Mọi lớp hiện tại");
  fillSelect($("#scd-lop"), lops, "lop", (row) => row.lop);

  // Mặc định chọn B23DCKD004 (Nguyễn Quý Tường Anh) để kiểm chứng SCD Type 2
  const hsSel = $("#hs-select");
  const scdHs = $("#scd-hs");
  if (hsSel && [...hsSel.options].some((opt) => opt.value === "B23DCKD004")) hsSel.value = "B23DCKD004";
  if (scdHs && [...scdHs.options].some((opt) => opt.value === "B23DCKD004")) scdHs.value = "B23DCKD004";

  updateExamSummary();
}

function renderDashboard(data) {
  const kpis = $("#kpis");
  if (kpis) {
    const k = data.kpi || {};
    const p = data.pipeline || {};
    const cards = [
      ["Lượt thi đã nạp (Fact)", p.fact_bai || 0],
      ["Điểm trung bình toàn kho", k.diem_tb || 0],
      ["Phiên học đã nạp (Fact)", p.fact_phien || 0],
      ["Tổng thời lượng học (phút)", k.tong_phut || 0],
      ["Sinh viên đang theo dõi", k.hoc_sinh_hien_tai || 0],
      ["Phiên bản SCD Type 2", k.phien_ban_scd || 0],
    ];
    kpis.innerHTML = cards.map(([name, value]) => `
      <div class="kpi-card">
        <span>${esc(name)}</span>
        <b>${num(value)}</b>
      </div>
    `).join("");
  }
  bars($("#bars-mon"), data.theo_mon, "ten_mon", "diem_tb");
  bars($("#bars-ngay"), data.theo_ngay, "ngay", "so_luot");
}

function renderOlap(data) {
  const title = $("#olap-title");
  const note = $("#olap-note");
  const sql = $("#olap-sql");
  const result = $("#olap-result");
  if (title) title.textContent = data.thao_tac || "Kết quả phân tích";
  if (note) note.textContent = data.mo_ta || "";
  if (sql) sql.textContent = data.sql || "";
  if (!result) return;
  if (data.kieu === "pivot") {
    const head = ["<th></th>", ...(data.cot || []).map((col) => `<th>${esc(col)}</th>`)].join("");
    const body = (data.hang || []).map((hang, i) => {
      const cells = (data.matran[i] || []).map((value) => `<td>${value === null ? "–" : num(value)}</td>`).join("");
      return `<tr><th>${esc(hang)}</th>${cells}</tr>`;
    }).join("");
    result.innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
    return;
  }
  result.innerHTML = table(data.cot || [], data.dong || []);
}

function renderFanout(sample, summary) {
  const fanout = $("#fanout");
  if (!fanout) return;
  if (!sample) {
    fanout.innerHTML = "<strong>Đối chiếu:</strong> Toàn bộ kho dữ liệu có <b>" + (summary.ca_hai || 0) + "</b> cặp có cả điểm thi và chuyên cần, <b>" + (summary.chi_co_diem || 0) + "</b> cặp chỉ có điểm thi, <b>" + (summary.chi_co_chuyen_can || 0) + "</b> cặp chỉ có chuyên cần.";
    return;
  }
  fanout.innerHTML = `
    <strong>Minh họa chống bẫy Fan-Out trên cặp (${esc(sample.ma_hoc_sinh)} – ${esc(sample.ma_mon)}):</strong><br>
    • Thực tế: Sinh viên có <b>${sample.so_luot_thi}</b> bài thi (tổng điểm <b>${num(sample.tong_diem_dung)}</b>) và <b>${sample.so_phien}</b> phiên học (tổng phút <b>${num(sample.tong_phut_dung)}</b>).<br>
    • Nếu <em>JOIN trực tiếp hai Fact</em>: Tích số tạo thành <b>${num(sample.so_dong_khi_join_thang)} dòng</b> (thổi phồng tổng điểm lên <b>${num(sample.tong_diem_bi_nhan)}</b> và tổng phút lên <b>${num(sample.tong_phut_bi_nhan)}</b>).<br>
    • Kỹ thuật <strong>Drill-Across</strong>: Tổng hợp độc lập từng Fact rồi <code>FULL OUTER JOIN</code> giúp loại trừ hoàn toàn sai số.
  `;
}

async function loadDashboard() {
  if (!$("#page-dash")) return;
  try {
    const data = await api("/api/dashboard");
    renderDashboard(data);
  } catch (err) {
    toast(err.message, false);
  }
}

async function loadQuiz() {
  const deSel = $("#de-select");
  const quiz = $("#quiz");
  if (!deSel || !quiz) return;
  if (!deSel.value) return;
  updateExamSummary();
  try {
    const data = await api(`/api/de-thi/${deSel.value}/cau-hoi`);
    state.questions = data.cau_hoi || [];
    state.started = Date.now();
    if (!state.questions.length) {
      quiz.innerHTML = "<p class='empty-state'>Đề thi hiện chưa có câu hỏi.</p>";
      return;
    }
    quiz.innerHTML = state.questions.map((q, index) => `
      <div class="quiz-q">
        <p><b>Câu ${index + 1}:</b> ${esc(q.noi_dung)}</p>
        <div class="quiz-choices">
          ${["a", "b", "c", "d"].map((key) => `
            <label class="choice">
              <input type="radio" name="q${q.ma_cau}" value="${key.toUpperCase()}">
              <span><b>${key.toUpperCase()}.</b> ${esc(q[`phuong_an_${key}`])}</span>
            </label>
          `).join("")}
        </div>
      </div>
    `).join("") + `
      <button type="button" id="btn-nop" class="btn-primary">Nộp bài thi</button>
      <div id="quiz-result"></div>
    `;
  } catch (err) {
    quiz.innerHTML = `<p class='empty-state'>Lỗi tải câu hỏi: ${esc(err.message)}</p>`;
  }
}

function renderLesson() {
  const baiSel = $("#bai-select");
  const lesson = $("#lesson");
  if (!baiSel || !lesson || !state.meta) return;
  const bai = (state.meta.bai_hoc || []).find((row) => row.ma_bai === baiSel.value);
  if (!bai) {
    lesson.innerHTML = "<div class='empty-state'>Vui lòng chọn bài học từ danh mục.</div>";
    return;
  }
  state.tuongTac = 1;
  const defaultMin = Math.max(1, Math.round(bai.thoi_luong_phut * 0.8));
  lesson.innerHTML = `
    <div class="lesson-info">
      <h3>${esc(bai.ten_bai)}</h3>
      <p class="subtext">Loại bài: <b>${esc(bai.loai_noi_dung)}</b> &nbsp;|&nbsp; Thời lượng quy chuẩn: <b>${bai.thoi_luong_phut} phút</b></p>
    </div>
    <div class="lesson-control" style="margin-top: 14px;">
      <label class="field-label" for="lesson-min">Thời gian sinh viên đã học (phút):</label>
      <input id="lesson-min" type="number" min="1" max="${bai.thoi_luong_phut * 2}" value="${defaultMin}" style="width: 140px;">
    </div>
    <div class="lesson-control" style="margin-top: 12px;">
      <span class="field-label">Ghi nhận mức độ tương tác:</span>
      <p style="font-size: 14px;">Số lần tương tác: <b id="tap-count" style="color: var(--color-primary); font-size: 16px;">1</b></p>
    </div>
    <div class="lesson-actions">
      <button type="button" id="btn-tap" class="btn-secondary">➕ Thêm tương tác</button>
      <button type="button" id="btn-phien" class="btn-primary">✓ Hoàn thành phiên học</button>
    </div>
    <div id="lesson-result" class="hint-msg"></div>
  `;
}

async function loadScd() {
  const scdHs = $("#scd-hs");
  if (!scdHs) return;
  const ma = scdHs.value;
  if (!ma) return;

  const scdLop = $("#scd-lop");
  const scdTt = $("#scd-tt");
  if (state.meta && scdLop && scdTt) {
    const student = (state.meta.hoc_sinh || []).find((row) => row.ma_hs === ma);
    if (student) {
      scdLop.value = student.lop;
      scdTt.value = student.trang_thai_hoc_vu;
    }
  }

  const scdTable = $("#scd-table");
  const scdFacts = $("#scd-facts");
  if (!scdTable && !scdFacts) return; // Nếu đang ở cổng LMS thì không có bảng BI
  try {
    const data = await api(`/api/hoc-sinh/${ma}/scd`);
    if (scdTable) {
      scdTable.innerHTML = table(
        ["Phiên bản", "Lớp", "Trạng thái học vụ", "Lý do biến động", "Ngày bắt đầu", "Ngày kết thúc", "Hiệu lực", "Surrogate Key"],
        (data.phien_ban || []).map((row) => [row.version_no, row.lop, row.trang_thai_hoc_vu, row.ly_do, row.start_date, row.end_date, row.is_current, row.hoc_sinh_key]),
        (row) => (row[6] ? "current" : ""),
      );
    }
    if (scdFacts) {
      scdFacts.innerHTML = table(
        ["Ngày nộp bài", "Tên đề thi", "Điểm số", "Khóa ngoại gắn vào Fact", "Phiên bản lúc thi", "Lớp tại thời điểm thi", "Trạng thái lúc thi"],
        (data.bai_gan_day || []).map((row) => [row.ngay, row.ten_de, row.diem_so, row.hoc_sinh_key, row.version_no, row.lop, row.trang_thai_hoc_vu]),
      );
    }
  } catch (err) {
    if (scdTable) scdTable.innerHTML = `<p class='empty-state'>${esc(err.message)}</p>`;
    if (scdFacts) scdFacts.innerHTML = "";
  }
}

async function loadQuality() {
  if (!$("#page-chat")) return;
  try {
    const data = await api("/api/chat-luong");
    const qKpis = $("#q-kpis");
    if (qKpis) {
      const cards = [
        ["Tổng bài thi nguồn (OLTP)", data.tong.src_exam || 0],
        ["Bài thi đã nạp vào Fact", data.tong.loaded_exam || 0],
        ["Bản ghi bị Quality Gate loại", data.tong.rejected_exam || 0],
        ["Bất biến Nguồn = Nạp + Loại", data.khop_summary ? "BẢO TOÀN (100%)" : "LỆCH"],
      ];
      qKpis.innerHTML = cards.map(([name, value]) => `
        <div class="kpi-card">
          <span>${esc(name)}</span>
          <b>${typeof value === "number" ? num(value) : esc(value)}</b>
        </div>
      `).join("");
    }
    const qBatch = $("#q-batch");
    if (qBatch) {
      qBatch.innerHTML = table(
        ["Batch ID", "Trigger", "Bài nguồn", "Nạp Fact", "Bị loại", "Phiên nạp", "SCD mới", "Thời gian (ms)", "Trạng thái"],
        (data.me || []).map((row) => [row.batch_id, row.trigger_name, row.src_exam, row.loaded_exam, row.rejected_exam, row.loaded_session, row.scd_new, row.duration_ms, row.status]),
      );
    }
    const qReject = $("#q-reject");
    if (qReject) {
      qReject.innerHTML = table(
        ["Mã Reject", "Nguồn", "Mã nguồn", "Lý do từ chối (7 luật Quality Gate)", "Thời điểm phát hiện"],
        (data.loai || []).map((row) => [row.id, row.nguon, row.nguon_id, row.ly_do, row.created_at]),
      );
    }
    const qPlan = $("#q-plan");
    if (qPlan) {
      try {
        const plan = await api("/api/chat-luong/explain");
        qPlan.textContent = Object.entries(plan).map(([name, item]) => `=== ${name} ===\n${item.sql}\n${(item.ke_hoach || []).join("\n")}`).join("\n\n");
      } catch (err) {
        qPlan.textContent = err.message;
      }
    }
  } catch (err) {
    toast(err.message, false);
  }
}

function filters() {
  return {
    nguon: $("#f-nguon") ? $("#f-nguon").value : "ket_qua",
    muc: $("#f-muc") ? $("#f-muc").value : "thang",
    ma_mon: $("#f-mon") ? $("#f-mon").value : "",
    lop: $("#f-lop") ? $("#f-lop").value : "",
    tu_ngay: $("#f-tu") ? $("#f-tu").value : "",
    den_ngay: $("#f-den") ? $("#f-den").value : "",
  };
}

function shiftMuc(step) {
  const fMuc = $("#f-muc");
  if (!fMuc) return "thang";
  const levels = ["ngay", "tuan", "thang", "hoc_ky", "nam"];
  const index = Math.min(levels.length - 1, Math.max(0, levels.indexOf(fMuc.value) + step));
  fMuc.value = levels[index];
  return levels[index];
}

function connect() {
  const dot = $("#ws-dot");
  const text = $("#ws-text");
  if (!dot && !text) return;
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${proto}://${location.host}/ws/live`);
  socket.onopen = () => {
    if (dot) dot.classList.add("on");
    if (text) text.textContent = "Kho đang kết nối trực tiếp";
    socket.send("ping");
  };
  socket.onmessage = (message) => {
    try {
      const event = JSON.parse(message.data);
      if (event.type === "etl") {
        if ($("#page-dash") && $("#page-dash").classList.contains("active")) loadDashboard().catch(() => {});
        if ($("#page-chat") && $("#page-chat").classList.contains("active")) loadQuality().catch(() => {});
      }
    } catch (_e) {}
  };
  socket.onclose = () => {
    if (dot) dot.classList.remove("on");
    if (text) text.textContent = "Mất kết nối kho";
    setTimeout(connect, 2000);
  };
}

// Chuyển trang BI
function showBiPage(page) {
  const target = $(`#page-${page}`);
  if (!target) return;
  $$(".bi-section").forEach((el) => el.classList.remove("active"));
  target.classList.add("active");
  $$(".bi-nav-item").forEach((btn) => btn.classList.toggle("active", btn.dataset.page === page));

  if (page === "dash") loadDashboard().catch((err) => toast(err.message, false));
  if (page === "scd") {
    loadScd().catch((err) => toast(err.message, false));
    if ($("#btn-across")) $("#btn-across").click();
  }
  if (page === "olap") {
    const defaultPreset = document.querySelector(".btn-preset[data-preset='roll-up']");
    if (defaultPreset && !$("#olap-result").hasChildNodes()) defaultPreset.click();
  }
  if (page === "chat") loadQuality().catch((err) => toast(err.message, false));
}

// Chuyển tab LMS
function showLmsTab(tab) {
  const target = $(`#pane-${tab}`);
  if (!target) return;
  $$(".lms-tab-pane").forEach((el) => el.classList.remove("active"));
  target.classList.add("active");
  $$(".lms-nav-btn").forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tab));

  if (tab === "hoc") renderLesson();
  if (tab === "hocvu") {
    const hsSel = $("#hs-select");
    const scdHs = $("#scd-hs");
    if (hsSel && scdHs) scdHs.value = hsSel.value;
    loadScd().catch(() => {});
  }
}

document.addEventListener("click", async (event) => {
  // Navigation LMS Tabs
  const lmsTabBtn = event.target.closest(".lms-nav-btn[data-tab]");
  if (lmsTabBtn) {
    showLmsTab(lmsTabBtn.dataset.tab);
    return;
  }

  // Navigation BI Pages
  const biPageBtn = event.target.closest(".bi-nav-item[data-page]");
  if (biPageBtn) {
    showBiPage(biPageBtn.dataset.page);
    return;
  }

  // Preset OLAP buttons
  const presetBtn = event.target.closest("[data-preset]");
  if (presetBtn) {
    try {
      renderOlap(await api(`/api/olap/preset/${presetBtn.dataset.preset}`));
    } catch (err) {
      toast(err.message, false);
    }
    return;
  }

  // Refresh Dashboard
  if (event.target.id === "btn-refresh") {
    loadDashboard().then(() => toast("Đã làm mới số liệu Dashboard"));
    return;
  }

  // Nộp bài thi LMS
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
        body: JSON.stringify({
          ma_hs: $("#hs-select") ? $("#hs-select").value : "",
          ma_de: $("#de-select") ? $("#de-select").value : "",
          answers,
          thoi_gian_giay: seconds,
        }),
      });
      const qr = $("#quiz-result");
      if (qr) {
        const details = (data.ket_qua.chi_tiet || []).map((row, idx) => `
          <div>Câu ${idx + 1}: ${row.dung ? "<b style='color:#166534;'>Đúng ✓</b>" : "<b style='color:#dc2626;'>Sai ✗</b>"} (Chọn: ${row.chon || "Trống"} | Đáp án: ${row.dap_an})</div>
        `).join("");
        qr.innerHTML = `
          <div class="quiz-result-box">
            <div class="quiz-score-badge">Kết quả: ${num(data.ket_qua.diem)} / 10 điểm (Đúng ${data.ket_qua.so_cau_dung}/${data.ket_qua.tong_so_cau} câu)</div>
            <div class="quiz-detail-list">${details}</div>
          </div>
        `;
      }
      toast(`Đã nộp bài thành công! Điểm: ${data.ket_qua.diem}`);
    } catch (err) {
      toast(err.message, false);
    }
    return;
  }

  // Thêm tương tác bài học
  if (event.target.id === "btn-tap") {
    state.tuongTac += 1;
    const tc = $("#tap-count");
    if (tc) tc.textContent = state.tuongTac;
    return;
  }

  // Ghi phiên học LMS
  if (event.target.id === "btn-phien") {
    const minutes = Number($("#lesson-min") ? $("#lesson-min").value : 1);
    try {
      const data = await api("/api/hoc-tap/phien", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ma_hs: $("#hs-select") ? $("#hs-select").value : "",
          ma_bai: $("#bai-select") ? $("#bai-select").value : "",
          thoi_luong_giay: Math.max(60, minutes * 60),
          so_tuong_tac: state.tuongTac,
        }),
      });
      const lr = $("#lesson-result");
      if (lr) lr.textContent = `✓ Đã ghi nhận phiên học. Điểm chuyên cần đạt: ${num(data.diem_chuyen_can)}, video ghi nhận: ${data.so_video ? "Đạt yêu cầu" : "Chưa đủ thời lượng"}.`;
      toast("Đã ghi nhận phiên học thành công!");
    } catch (err) {
      toast(err.message, false);
    }
    return;
  }

  // Lưu thay đổi học vụ SCD2
  if (event.target.id === "btn-scd") {
    try {
      const data = await api("/api/admin/hoc-vu", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ma_hs: $("#scd-hs") ? $("#scd-hs").value : "",
          lop: $("#scd-lop") ? $("#scd-lop").value : "",
          trang_thai: $("#scd-tt") ? $("#scd-tt").value : "",
        }),
      });
      if (state.meta) {
        const student = (state.meta.hoc_sinh || []).find((row) => row.ma_hs === ($("#scd-hs") ? $("#scd-hs").value : ""));
        if (student) {
          if ($("#scd-lop")) student.lop = $("#scd-lop").value;
          if ($("#scd-tt")) student.trang_thai_hoc_vu = $("#scd-tt").value;
        }
      }
      const resMsg = $("#hocvu-result");
      if (resMsg) {
        resMsg.textContent = `✓ Hồ sơ đã được cập nhật thành công (Lý do biến động: ${data.ly_do || "Cập nhật học vụ"}).`;
      }
      toast(`Cập nhật thành công: ${data.ly_do || "OK"}`);
      await loadScd();
    } catch (err) {
      toast(err.message, false);
    }
    return;
  }

  // Thao tác OLAP tùy chỉnh
  if (["btn-rollup", "btn-drill", "btn-slice", "btn-dice", "btn-pivot", "btn-swap"].includes(event.target.id)) {
    try {
      if (event.target.id === "btn-rollup") shiftMuc(1);
      if (event.target.id === "btn-drill") shiftMuc(-1);
      if (event.target.id === "btn-swap" && $("#p-hang") && $("#p-cot")) {
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

      const body = {
        ...filters(),
        thao_tac: thao,
        kieu: thao === "Pivot" ? "pivot" : "bang",
        hang: $("#p-hang") ? $("#p-hang").value : "lop",
        cot: $("#p-cot") ? $("#p-cot").value : "mon",
      };

      if (thao === "Slice") {
        body.lop = "";
        body.tu_ngay = "";
        body.den_ngay = "";
        if (!body.ma_mon) body.ma_mon = "KDL";
      }
      if (thao === "Dice") {
        const used = [body.ma_mon, body.lop, body.tu_ngay && body.den_ngay].filter(Boolean).length;
        if (used < 2) {
          toast("Dice cần ít nhất hai điều kiện (ví dụ môn và lớp).", false);
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
    return;
  }

  // Chạy Drill-Across
  if (event.target.id === "btn-across") {
    try {
      const lop = $("#ax-lop") ? $("#ax-lop").value : "";
      const mon = $("#ax-mon") ? $("#ax-mon").value : "";
      const data = await api(`/api/olap/drill-across?lop=${encodeURIComponent(lop)}&ma_mon=${encodeURIComponent(mon)}`);
      const acrossTable = $("#across-table");
      if (acrossTable) acrossTable.innerHTML = table(data.cot, data.dong);
      renderFanout(data.vi_du_nhan_ban, data);
    } catch (err) {
      toast(err.message, false);
    }
    return;
  }
});

function bindStaticEvents() {
  const deSel = $("#de-select");
  if (deSel) deSel.addEventListener("change", () => loadQuiz().catch((err) => toast(err.message, false)));

  const baiSel = $("#bai-select");
  if (baiSel) baiSel.addEventListener("change", renderLesson);

  const hsSel = $("#hs-select");
  if (hsSel) hsSel.addEventListener("change", () => {
    const scd = $("#scd-hs");
    if (scd) {
      scd.value = hsSel.value;
      loadScd().catch(() => {});
    }
  });

  const scdHs = $("#scd-hs");
  if (scdHs) scdHs.addEventListener("change", () => loadScd().catch((err) => toast(err.message, false)));
}

async function boot() {
  try {
    bindStaticEvents();

    // Tải Metadata dùng chung
    const meta = await api("/api/meta");
    bindMeta(meta);

    // Nếu ở cổng LMS (/hoc-tap)
    if ($("#quiz")) await loadQuiz();
    if ($("#lesson")) renderLesson();

    // Nếu ở cổng BI (/bi)
    if ($("#page-dash")) await loadDashboard();
    if ($("#page-scd") && $("#scd-table")) await loadScd().catch(() => {});

    connect();
  } catch (err) {
    toast(err.message, false);
  }
}

boot();
