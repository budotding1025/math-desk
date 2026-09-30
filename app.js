/* 数学书桌 · 主页 / 路径 / 记录（对齐语文框架） */
(function () {
  const DATA = window.MATH_DESK_DATA;
  const DAILY = window.MATH_DAILY || [];
  const P = window.MathProgress;
  if (!DATA || !P) return;

  const $ = (id) => document.getElementById(id);
  const state = { view: "home", node: null, composeUnitId: "u02" }; // 教材第二单元：公顷和平方千米

  function showView(name) {
    state.view = name;
    ["Home", "Path", "Records"].forEach((k) => {
      const el = $("screen" + k);
      if (el) el.classList.toggle("hidden", name.toLowerCase() !== k.toLowerCase());
    });
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.classList.toggle("is-on", btn.dataset.nav === name);
    });
    if (name === "home") renderHome();
    if (name === "path") renderPath();
    if (name === "records") renderRecords();
  }

  function openPdf(url) {
    if (!url) return;
    window.open(url, "_blank");
  }

  function dailyBank(unitId) {
    return DAILY.find((u) => u.id === unitId) || DAILY[0];
  }

  function renderHome() {
    const store = P.ensure();
    const node = P.currentNode();
    state.node = node;
    $("streakLine").innerHTML = "连续 <strong>" + (store.streak.count || 0) + "</strong> 天";
    $("sessionEyebrow").textContent = node.unitTitle;
    $("sessionTitle").textContent =
      node.type === "daily"
        ? node.lessonLabel + " · 日常练习"
        : node.lessonLabel + " · 考前测试";
    $("sessionMeta").textContent =
      node.type === "daily" ? "今日练习 · 约 15 分钟" : "今日练习 · 30–40 分钟";
    $("unitLine").textContent = node.unitTitle;
    $("pathSummary").textContent =
      "路径 " + P.completedCount() + " / " + P.semesterPath().length + " 站已练";

    const primary = $("btnHomePrimary");
    const secondary = $("btnHomeSecondary");
    if (node.type === "daily") {
      primary.textContent = "开始组卷";
      primary.onclick = () => openCompose(node.unitId);
      secondary.textContent = "打开考卷";
      secondary.onclick = () => openPdf(node.unit.examPdf);
    } else {
      primary.textContent = "打开考卷";
      primary.onclick = () => {
        openPdf(node.unit.examPdf);
        P.markDone(node.id);
        renderHome();
      };
      secondary.textContent = "去组卷";
      secondary.onclick = () => openCompose(node.unitId);
    }
  }

  function renderPath() {
    const store = P.ensure();
    const path = P.semesterPath();
    $("pathMeta").textContent =
      "共 " + path.length + " 站（每单元：日常练习 + 考前测试）· 已练 " + P.completedCount() + " 站";
    const host = $("pathList");
    host.innerHTML = "";
    let lastUnit = "";
    const cur = P.currentNode();
    path.forEach((node) => {
      if (node.unitTitle !== lastUnit) {
        lastUnit = node.unitTitle;
        const h = document.createElement("div");
        h.className = "path-unit";
        h.textContent = node.unitTitle;
        host.appendChild(h);
      }
      const done = store.completed[node.id] && store.completed[node.id].count > 0;
      const current = cur && cur.id === node.id;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "path-node" + (done ? " is-done" : "") + (current ? " is-current" : "");
      const badge = node.type === "daily" ? "练" : "测";
      btn.innerHTML =
        '<span class="path-badge">' +
        badge +
        '</span><span class="path-copy"><strong>' +
        node.lessonLabel +
        " · " +
        node.title +
        "</strong><small>" +
        node.kind +
        (done ? " · 已练" : "") +
        (current ? " · 当前" : "") +
        "</small></span>";
      btn.addEventListener("click", () => openNodePicker(node));
      host.appendChild(btn);
    });
  }

  function openNodePicker(node) {
    state.node = node;
    $("pathNodeTitle").textContent = node.lessonLabel + " · " + node.title;
    $("pathNodeMeta").textContent = node.unitTitle + " · " + node.kind;
    const grid = $("pathModGrid");
    grid.innerHTML = "";

    if (node.type === "daily") {
      const a = document.createElement("button");
      a.type = "button";
      a.className = "mod-btn";
      a.innerHTML = "日常练习 · 组卷打印<small>选 ①②③ · 排成 A4 · 约 15 分钟</small>";
      a.onclick = () => {
        $("pathNodeOverlay").classList.add("hidden");
        openCompose(node.unitId);
      };
      grid.appendChild(a);
    } else {
      const a = document.createElement("button");
      a.type = "button";
      a.className = "mod-btn";
      a.innerHTML =
        "打开考前测试 PDF<small>" +
        (node.unit.examComplete ? "完整卷" : "部分卷") +
        " · 30–40 分钟</small>";
      a.onclick = () => {
        openPdf(node.unit.examPdf);
        P.markDone(node.id);
        $("pathNodeOverlay").classList.add("hidden");
      };
      grid.appendChild(a);
    }

    const setCur = document.createElement("button");
    setCur.type = "button";
    setCur.className = "mod-btn";
    setCur.innerHTML = "设为当前进度<small>主页显示这一站</small>";
    setCur.onclick = () => {
      P.setCurrent(node.unitId, node.type);
      $("pathNodeOverlay").classList.add("hidden");
      showView("home");
    };
    grid.appendChild(setCur);

    $("pathNodeOverlay").classList.remove("hidden");
  }

  function renderRecords() {
    const store = P.ensure();
    $("recordsScore").innerHTML =
      "连续 <b>" +
      (store.streak.count || 0) +
      "</b> 天 · 路径已练 <b>" +
      P.completedCount() +
      "</b> 站<br/><span style='color:var(--muted);font-size:.88rem'>错题分「计算错 / 概念错」更好订正</span>";

    const actions = $("recordsActions");
    actions.innerHTML = "";
    DATA.units.forEach((u) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "rec-card";
      b.innerHTML = "<strong>" + u.name + "</strong><br/><small style='color:var(--muted)'>错题重练纸 · PDF</small>";
      b.onclick = () => openPdf(u.wrongPdf);
      actions.appendChild(b);
    });

    const sel = $("mistakeUnit");
    sel.innerHTML = DATA.units
      .map((u) => '<option value="' + u.id + '">' + u.name + "</option>")
      .join("");

    const list = $("recordsList");
    const mistakes = P.listMistakes();
    $("recordsMeta").textContent = "我的错题（" + mistakes.length + "）";
    if (!mistakes.length) {
      list.innerHTML = '<p class="meta" style="padding:8px 0">还没有登记错题。做完练习把错题记下来。</p>';
      return;
    }
    list.innerHTML = "";
    mistakes.forEach((m) => {
      const div = document.createElement("div");
      div.className = "mistake-item";
      div.innerHTML =
        '<div class="row"><div><span class="kind">' +
        (m.kind || "") +
        " · " +
        (m.unitTitle || "") +
        " · " +
        (m.at || "") +
        "</span><p style='margin:6px 0 0;font-weight:700'>" +
        (m.text || "") +
        "</p>" +
        (m.note ? "<p style='margin:4px 0 0;color:var(--muted);font-size:.88rem'>订正：" + m.note + "</p>" : "") +
        '</div><button type="button" class="del" data-id="' +
        m.id +
        '">删除</button></div>';
      list.appendChild(div);
    });
    list.querySelectorAll(".del").forEach((btn) => {
      btn.onclick = () => {
        P.removeMistake(btn.getAttribute("data-id"));
        renderRecords();
      };
    });
  }

  /* —— A4 组卷 —— */
  function selectedTracks() {
    return Array.from(document.querySelectorAll("#trackChecks input:checked")).map((el) => el.value);
  }
  function layoutMode() {
    const el = document.querySelector('#layoutMode input[name="layout"]:checked');
    return el ? el.value : "combine";
  }
  function updateHint() {
    const n = selectedTracks().length;
    if (!n) {
      $("selectHint").textContent = "请至少选择一项";
      return;
    }
    $("selectHint").textContent =
      layoutMode() === "split" && n > 1
        ? "已选 " + n + " 项 · 分项 " + n + " 页 · 每页约 15 分钟"
        : "已选 " + n + " 项 · 合订 1 页 · 合计约 15 分钟";
  }

  function openCompose(unitId) {
    state.composeUnitId = unitId;
    const u = P.unitById(unitId);
    $("composeTitle").textContent = u.name + " · 日常组卷";
    $("composeMeta").textContent = "约 15 分钟 · 选 ①②③ 排成 A4 打印 / 另存 PDF";
    updateHint();
    $("composeOverlay").classList.remove("hidden");
  }

  function trimItems(items, max) {
    return (items || []).slice(0, max);
  }

  /** 把过窄填空扩到考前卷同款留白（短／中／长） */
  function widenBlanks(text) {
    return String(text || "")
      .replace(/（[ \t]*）/g, "（　　）")
      .replace(/（　）/g, "（　　）")
      .replace(/_{3,7}(?!_)/g, "______________");
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function normalizeItem(raw) {
    if (raw && typeof raw === "object") {
      return {
        text: String(raw.text || raw.q || ""),
        img: raw.img || "",
        w: raw.w || "88%",
      };
    }
    return { text: String(raw || ""), img: "", w: "88%" };
  }

  function itemExtras(text, hasFig) {
    if (hasFig) {
      if (/画出|作图|在图上|标出/.test(text) && !/画“○”|画“△”/.test(text)) {
        /* 已有底图时，不再叠空白作图框，留给图上作答 */
      } else if (/写出|说明|答：|思路|步骤|描述|理由|情形/.test(text)) {
        return '<div class="write-area" aria-hidden="true"><span></span><span></span></div>';
      }
      return "";
    }
    if (/竖式/.test(text)) return '<div class="calc-box" aria-hidden="true"></div>';
    if (/画出|作图/.test(text)) return '<div class="draw-box" aria-hidden="true"></div>';
    if (/写出|说明|答：|思路|步骤|描述|理由|情形/.test(text)) {
      return '<div class="write-area" aria-hidden="true"><span></span><span></span><span></span></div>';
    }
    return "";
  }

  function itemHtml(raw) {
    const it = normalizeItem(raw);
    const stem = escapeHtml(widenBlanks(it.text));
    const fig = it.img
      ? '<div class="q-fig"><img src="' +
        escapeHtml(it.img) +
        '" alt="示意图" style="width:' +
        escapeHtml(it.w) +
        ';max-width:100%;height:auto" /></div>'
      : "";
    return (
      '<li class="q-item">' +
      '<div class="q-stem">' +
      stem +
      "</div>" +
      fig +
      itemExtras(it.text, !!it.img) +
      "</li>"
    );
  }

  function blockHtml(section, compact) {
    /* 合订多项时少取题；有图时更少，保证一张 A4 */
    const hasFig = (section.items || []).some((x) => x && typeof x === "object" && x.img);
    const max = compact ? (hasFig ? 2 : 3) : hasFig ? 4 : 6;
    const lis = trimItems(section.items, max).map(itemHtml).join("");
    return (
      '<div class="block' +
      (compact ? " compact" : "") +
      '"><h3>' +
      escapeHtml(section.title) +
      (compact ? "（精选）" : "") +
      '</h3><p class="sub">' +
      escapeHtml(section.hint || "") +
      '</p><ol class="q">' +
      lis +
      "</ol></div>"
    );
  }

  function sheetShell(unitTitle, body, meta, pageIndex, pageTotal) {
    return (
      '<article class="sheet-a4' +
      (pageIndex > 0 ? " page-break" : "") +
      '"><header class="sheet-head"><p class="sheet-brand">数学书桌 · Math Desk</p><p class="sheet-title">' +
      escapeHtml(unitTitle) +
      ' · 日常练习</p><p class="sheet-meta">' +
      escapeHtml(meta) +
      "　|　第 " +
      (pageIndex + 1) +
      " / " +
      pageTotal +
      ' 页　|　A4</p></header><p class="sheet-info">学校____________　四年级____班　姓名____________　日期____________</p>' +
      body +
      '<p class="sheet-foot">订正区：____________________________________________________________</p></article>'
    );
  }

  function buildAndPrint() {
    const tracks = selectedTracks();
    if (!tracks.length) {
      alert("请至少选择 ① / ② / ③ 中的一项");
      return;
    }
    const bank = dailyBank(state.composeUnitId);
    const sections = tracks.map((k) => bank[k]).filter(Boolean);
    const mode = layoutMode();
    let html = "";
    if (mode === "combine" || sections.length === 1) {
      const compact = sections.length > 1;
      const body = sections.map((s) => blockHtml(s, compact)).join("");
      const names = sections.map((s) => s.title).join(" + ");
      html = sheetShell(bank.title, body, "合订　|　" + names + "　|　约 15 分钟", 0, 1);
    } else {
      html = sections
        .map((s, i) =>
          sheetShell(bank.title, blockHtml(s, false), "分项　|　" + s.title + "　|　约 15 分钟", i, sections.length)
        )
        .join("");
    }
    $("printRoot").innerHTML = html;
    $("btnDownload").disabled = false;
    $("composeOverlay").classList.add("hidden");
    P.markDone(state.composeUnitId + "-daily");
    window.print();
  }

  function downloadHtml() {
    const bank = dailyBank(state.composeUnitId);
    const html =
      "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\" /><title>" +
      bank.title +
      " · 日常练习</title><link rel=\"stylesheet\" href=\"theme.css\" /></head><body class=\"print-root\" style=\"display:block\">" +
      $("printRoot").innerHTML +
      "<script>onload=function(){print()}<\/script></body></html>";
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = state.composeUnitId + "-日常练习-A4.html";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /* events */
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => showView(btn.dataset.nav));
  });
  $("btnOpenPath").onclick = () => showView("path");
  $("pathNodeClose").onclick = () => $("pathNodeOverlay").classList.add("hidden");
  $("composeClose").onclick = () => $("composeOverlay").classList.add("hidden");
  $("btnSettings").onclick = () => $("helpOverlay").classList.remove("hidden");
  $("btnCloseHelp").onclick = () => $("helpOverlay").classList.add("hidden");
  document.querySelectorAll("#trackChecks input, #layoutMode input").forEach((el) => {
    el.addEventListener("change", updateHint);
  });
  $("btnBuild").onclick = buildAndPrint;
  $("btnDownload").onclick = downloadHtml;
  $("mistakeForm").onsubmit = (e) => {
    e.preventDefault();
    const unit = P.unitById($("mistakeUnit").value);
    const text = ($("mistakeText").value || "").trim();
    if (!text) {
      alert("请填写错题摘录");
      return;
    }
    P.addMistake({
      unitId: unit.id,
      unitTitle: unit.name,
      kind: $("mistakeKind").value,
      text: text,
      note: ($("mistakeNote").value || "").trim(),
    });
    $("mistakeText").value = "";
    $("mistakeNote").value = "";
    renderRecords();
  };

  showView("home");
})();
