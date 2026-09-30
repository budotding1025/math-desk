/* 数学书桌 · 主页 / 路径 / 记录（错题拍照入库 + 原题/类似题） */
(function () {
  const DATA = window.MATH_DESK_DATA;
  const DAILY = window.MATH_DAILY || [];
  const P = window.MathProgress;
  const W = window.WrongStore;
  if (!DATA || !P || !W) return;

  const $ = (id) => document.getElementById(id);
  const state = {
    view: "home",
    node: null,
    composeUnitId: "u02",
    pendingPhotoBlob: null,
    pendingPhotoUrl: "",
    photoViewId: "",
    objectUrls: [],
    mark: {
      pages: [], // ImageBitmap | HTMLCanvasElement | HTMLImageElement
      pageIndex: 0,
      strokes: [], // strokes[page] = [[{x,y},...], ...]
      drawing: false,
      ready: false,
    },
  };

  const RED_PEN = "#dc2626";
  const RED_WIDTH = 4;

  const SOURCE_LABEL = {
    "daily-calc": "日常 · ① 计算",
    "daily-key": "日常 · ② 重难点",
    "daily-app": "日常 · ③ 应用题",
    exam: "考前测试",
  };

  function trackFromSource(source) {
    if (source === "daily-calc") return "calc";
    if (source === "daily-key") return "key";
    if (source === "daily-app") return "app";
    return "";
  }

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

  function itemText(raw) {
    if (raw && typeof raw === "object") return String(raw.text || raw.q || "");
    return String(raw || "");
  }

  function sourceItemCount(unitId, source) {
    if (source === "exam") {
      const u = P.unitById(unitId);
      const pages = (u && u.examPages) || 4;
      return Math.max(12, pages * 6);
    }
    const track = trackFromSource(source);
    const bank = dailyBank(unitId);
    const section = bank && bank[track];
    return (section && section.items && section.items.length) || 6;
  }

  function paperUrlFor(unitId, source) {
    const u = P.unitById(unitId);
    if (!u) return "";
    if (source === "exam") return u.examPdf || "";
    return "";
  }

  function markInkHasAny() {
    return state.mark.strokes.some((page) => page && page.length);
  }

  function setMarkHint(text, show) {
    const hint = $("markPaperHint");
    if (!hint) return;
    hint.textContent = text || "";
    hint.classList.toggle("hidden", !show);
  }

  function fitMarkCanvases(w, h) {
    const base = $("markBase");
    const ink = $("markInk");
    const stage = $("markStage");
    const wrap = $("markStageWrap");
    const maxW = Math.max(280, (wrap && wrap.clientWidth) || 640) - 8;
    const scale = Math.min(1, maxW / w);
    const cssW = Math.round(w * scale);
    const cssH = Math.round(h * scale);
    [base, ink].forEach((c) => {
      c.width = w;
      c.height = h;
      c.style.width = cssW + "px";
      c.style.height = cssH + "px";
    });
    stage.style.width = cssW + "px";
    stage.style.height = cssH + "px";
  }

  function drawMarkBase() {
    const page = state.mark.pages[state.mark.pageIndex];
    const base = $("markBase");
    const ctx = base.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, base.width, base.height);
    if (!page) return;
    ctx.drawImage(page, 0, 0, base.width, base.height);
  }

  function drawMarkInk() {
    const ink = $("markInk");
    const ctx = ink.getContext("2d");
    ctx.clearRect(0, 0, ink.width, ink.height);
    const strokes = state.mark.strokes[state.mark.pageIndex] || [];
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = RED_PEN;
    ctx.lineWidth = RED_WIDTH;
    strokes.forEach((stroke) => {
      if (!stroke || stroke.length < 2) {
        if (stroke && stroke.length === 1) {
          ctx.beginPath();
          ctx.fillStyle = RED_PEN;
          ctx.arc(stroke[0].x, stroke[0].y, RED_WIDTH / 2, 0, Math.PI * 2);
          ctx.fill();
        }
        return;
      }
      ctx.beginPath();
      ctx.moveTo(stroke[0].x, stroke[0].y);
      for (let i = 1; i < stroke.length; i++) ctx.lineTo(stroke[i].x, stroke[i].y);
      ctx.stroke();
    });
  }

  function showMarkPage() {
    const n = state.mark.pages.length;
    const i = state.mark.pageIndex;
    $("markPrevPage").hidden = n <= 1;
    $("markNextPage").hidden = n <= 1;
    $("markPageLabel").textContent = n ? i + 1 + " / " + n : "";
    if (!n) return;
    const page = state.mark.pages[i];
    const w = page.width || page.naturalWidth || 794;
    const h = page.height || page.naturalHeight || 1123;
    fitMarkCanvases(w, h);
    drawMarkBase();
    drawMarkInk();
    setMarkHint("", false);
  }

  function inkPointFromEvent(e) {
    const ink = $("markInk");
    const rect = ink.getBoundingClientRect();
    const src = e.touches && e.touches[0] ? e.touches[0] : e;
    const x = ((src.clientX - rect.left) / rect.width) * ink.width;
    const y = ((src.clientY - rect.top) / rect.height) * ink.height;
    return { x: x, y: y };
  }

  function ensurePageStrokes() {
    while (state.mark.strokes.length < state.mark.pages.length) state.mark.strokes.push([]);
  }

  function bindMarkInkOnce() {
    const ink = $("markInk");
    if (ink.dataset.bound === "1") return;
    ink.dataset.bound = "1";

    const start = (e) => {
      if (!state.mark.ready) return;
      e.preventDefault();
      try {
        ink.setPointerCapture(e.pointerId);
      } catch (err) {
        /* ignore */
      }
      ensurePageStrokes();
      state.mark.drawing = true;
      const p = inkPointFromEvent(e);
      state.mark.strokes[state.mark.pageIndex].push([p]);
      drawMarkInk();
    };
    const move = (e) => {
      if (!state.mark.drawing) return;
      e.preventDefault();
      const strokes = state.mark.strokes[state.mark.pageIndex];
      const cur = strokes[strokes.length - 1];
      if (!cur) return;
      cur.push(inkPointFromEvent(e));
      drawMarkInk();
    };
    const end = () => {
      state.mark.drawing = false;
    };

    ink.addEventListener("pointerdown", start);
    ink.addEventListener("pointermove", move);
    ink.addEventListener("pointerup", end);
    ink.addEventListener("pointercancel", end);
    ink.addEventListener("pointerleave", end);
  }

  async function loadImageFromBlob(blob) {
    const url = URL.createObjectURL(blob);
    try {
      const img = new Image();
      img.decoding = "async";
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = reject;
        img.src = url;
      });
      return img;
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  async function renderPdfPages(url) {
    if (!window.pdfjsLib) throw new Error("pdf.js missing");
    if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
      pdfjsLib.GlobalWorkerOptions.workerSrc =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
    }
    const doc = await pdfjsLib.getDocument(url).promise;
    const pages = [];
    for (let i = 1; i <= doc.numPages; i++) {
      const page = await doc.getPage(i);
      const viewport = page.getViewport({ scale: 1.35 });
      const canvas = document.createElement("canvas");
      canvas.width = Math.floor(viewport.width);
      canvas.height = Math.floor(viewport.height);
      await page.render({ canvasContext: canvas.getContext("2d"), viewport: viewport }).promise;
      pages.push(canvas);
    }
    return pages;
  }

  function buildDailyPaper(unitId, source) {
    const track = trackFromSource(source);
    const bank = dailyBank(unitId);
    const section = bank && bank[track];
    const items = (section && section.items) || [];
    const unit = P.unitById(unitId);
    const canvas = document.createElement("canvas");
    canvas.width = 794;
    canvas.height = Math.max(1123, 160 + items.length * 88);
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#12344a";
    ctx.font = "bold 28px sans-serif";
    ctx.fillText((unit && unit.short) || "日常练习", 40, 48);
    ctx.font = "18px sans-serif";
    ctx.fillStyle = "#5a7a8c";
    ctx.fillText(SOURCE_LABEL[source] || "日常", 40, 78);
    ctx.strokeStyle = "#cfe6f4";
    ctx.beginPath();
    ctx.moveTo(40, 92);
    ctx.lineTo(canvas.width - 40, 92);
    ctx.stroke();

    let y = 130;
    ctx.fillStyle = "#12344a";
    items.forEach((raw, idx) => {
      const text = idx + 1 + ". " + itemText(raw);
      ctx.font = "20px sans-serif";
      const lines = wrapText(ctx, text, canvas.width - 100);
      lines.forEach((line, li) => {
        ctx.fillText(line, 48, y + li * 28);
      });
      y += Math.max(72, lines.length * 28 + 24);
    });
    return canvas;
  }

  function wrapText(ctx, text, maxWidth) {
    const chars = String(text || "").split("");
    const lines = [];
    let line = "";
    chars.forEach((ch) => {
      const test = line + ch;
      if (ctx.measureText(test).width > maxWidth && line) {
        lines.push(line);
        line = ch;
      } else line = test;
    });
    if (line) lines.push(line);
    return lines.length ? lines : [""];
  }

  async function loadMarkPages() {
    state.mark.ready = false;
    state.mark.pages = [];
    state.mark.pageIndex = 0;
    state.mark.strokes = [];
    state.mark.drawing = false;
    setMarkHint("正在打开卷面…", true);

    const unitId = $("markUnit").value;
    const source = $("markSource").value;

    try {
      if (source === "exam") {
        const url = paperUrlFor(unitId, source);
        if (!url) throw new Error("no exam pdf");
        state.mark.pages = await renderPdfPages(url);
      } else {
        state.mark.pages = [buildDailyPaper(unitId, source)];
      }
      state.mark.strokes = state.mark.pages.map(() => []);
      state.mark.ready = true;
      showMarkPage();
    } catch (err) {
      console.error(err);
      state.mark.pages = [];
      state.mark.ready = false;
      setMarkHint("卷面打不开时，可点「用照片当卷面」拍打印好的纸，再红笔圈题。", true);
    }
  }

  function openMarkSheet(opts) {
    opts = opts || {};
    bindMarkInkOnce();
    const sel = $("markUnit");
    sel.innerHTML = DATA.units
      .map((u) => '<option value="' + u.id + '">' + u.name + "</option>")
      .join("");
    const preferUnit =
      opts.unitId ||
      (state.node && state.node.unitId) ||
      (P.currentNode() && P.currentNode().unitId) ||
      DATA.currentUnitId;
    if (preferUnit && DATA.units.some((u) => u.id === preferUnit)) sel.value = preferUnit;

    let preferSource = opts.source || "exam";
    if (!opts.source && state.node) {
      preferSource = state.node.type === "exam" ? "exam" : "daily-calc";
    }
    $("markSource").value = preferSource;
    $("markMeta").textContent = "在原卷上用红笔画圈，圈完点「记上了」";
    $("markOverlay").classList.remove("hidden");
    loadMarkPages();
  }

  function undoMarkStroke() {
    ensurePageStrokes();
    const strokes = state.mark.strokes[state.mark.pageIndex];
    if (!strokes || !strokes.length) return;
    strokes.pop();
    drawMarkInk();
  }

  function clearMarkInk() {
    ensurePageStrokes();
    state.mark.strokes[state.mark.pageIndex] = [];
    drawMarkInk();
  }

  function compositeMarkedBlob() {
    return new Promise((resolve, reject) => {
      const marked = [];
      state.mark.pages.forEach((page, idx) => {
        if (!(state.mark.strokes[idx] && state.mark.strokes[idx].length)) return;
        marked.push(idx);
      });
      const use = marked.length ? marked : [state.mark.pageIndex];
      let totalH = 0;
      let maxW = 0;
      const dims = use.map((idx) => {
        const page = state.mark.pages[idx];
        const w = page.width || page.naturalWidth;
        const h = page.height || page.naturalHeight;
        maxW = Math.max(maxW, w);
        totalH += h + 12;
        return { idx: idx, w: w, h: h };
      });
      const out = document.createElement("canvas");
      out.width = maxW;
      out.height = Math.max(totalH - 12, 1);
      const ctx = out.getContext("2d");
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, out.width, out.height);
      let y = 0;
      dims.forEach((d) => {
        const page = state.mark.pages[d.idx];
        const tmp = document.createElement("canvas");
        tmp.width = d.w;
        tmp.height = d.h;
        const tctx = tmp.getContext("2d");
        tctx.fillStyle = "#fff";
        tctx.fillRect(0, 0, d.w, d.h);
        tctx.drawImage(page, 0, 0, d.w, d.h);
        tctx.lineCap = "round";
        tctx.lineJoin = "round";
        tctx.strokeStyle = RED_PEN;
        tctx.lineWidth = RED_WIDTH;
        (state.mark.strokes[d.idx] || []).forEach((stroke) => {
          if (!stroke || !stroke.length) return;
          if (stroke.length === 1) {
            tctx.beginPath();
            tctx.fillStyle = RED_PEN;
            tctx.arc(stroke[0].x, stroke[0].y, RED_WIDTH / 2, 0, Math.PI * 2);
            tctx.fill();
            return;
          }
          tctx.beginPath();
          tctx.moveTo(stroke[0].x, stroke[0].y);
          for (let i = 1; i < stroke.length; i++) tctx.lineTo(stroke[i].x, stroke[i].y);
          tctx.stroke();
        });
        ctx.drawImage(tmp, 0, y);
        y += d.h + 12;
      });
      out.toBlob(
        (blob) => (blob ? resolve(blob) : reject(new Error("blob failed"))),
        "image/jpeg",
        0.88
      );
    });
  }

  async function saveMarkSheet() {
    if (!state.mark.ready || !state.mark.pages.length) {
      alert("请先打开卷面，或用照片当卷面");
      return;
    }
    if (!markInkHasAny()) {
      alert("先用红笔在卷面上圈出错的题");
      return;
    }
    const unit = P.unitById($("markUnit").value);
    const source = $("markSource").value;
    const blob = await compositeMarkedBlob();
    const photoId = await W.savePhotoBlob(blob);
    await W.putMistake({
      unitId: unit.id,
      unitTitle: unit.name,
      source: source,
      kind: "其他",
      itemNos: [],
      text: (SOURCE_LABEL[source] || "练习") + " · 原卷红笔圈题",
      note: "",
      photoId: photoId,
    });
    $("markOverlay").classList.add("hidden");
    showView("records");
  }

  function excerptFromBank(unitId, source, itemNos) {
    const track = trackFromSource(source);
    if (!track) return "";
    const bank = dailyBank(unitId);
    const section = bank && bank[track];
    if (!section || !section.items) return "";
    const lines = [];
    (itemNos || []).forEach((n) => {
      const raw = section.items[n - 1];
      if (raw != null) lines.push(itemText(raw));
    });
    return lines.join("\n");
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
      secondary.textContent = node.unit.examAnswerPdf ? "打印答案" : "去组卷";
      secondary.onclick = () => {
        if (node.unit.examAnswerPdf) openPdf(node.unit.examAnswerPdf);
        else openCompose(node.unitId);
      };
    }
  }

  function renderPath() {
    const store = P.ensure();
    const path = P.semesterPath();
    $("pathMeta").textContent =
      "共 " +
      path.length +
      " 站（每单元：日常 + 考前）· 已练 " +
      P.completedCount() +
      " 站 · 做完红笔批改 → 记录页勾题入库";
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
    $("pathNodeMeta").textContent =
      node.unitTitle + " · " + node.kind + " · 做完后在原卷上用红笔圈错题";
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
      const pages = node.unit.examPages || 0;
      a.innerHTML =
        "打开考前测试（试卷）<small>" +
        (node.unit.examComplete ? "完整 " : "部分 ") +
        (pages ? pages + " 页 · 对齐上传 JPG" : "待补") +
        " · 30–40 分钟</small>";
      a.onclick = () => {
        openPdf(node.unit.examPdf);
        P.markDone(node.id);
        $("pathNodeOverlay").classList.add("hidden");
      };
      grid.appendChild(a);
      if (node.unit.examAnswerPdf) {
        const ans = document.createElement("button");
        ans.type = "button";
        ans.className = "mod-btn";
        ans.innerHTML = "打印参考答案<small>单独答案页</small>";
        ans.onclick = () => {
          openPdf(node.unit.examAnswerPdf);
          $("pathNodeOverlay").classList.add("hidden");
        };
        grid.appendChild(ans);
      }
    }

    const toRec = document.createElement("button");
    toRec.type = "button";
    toRec.className = "mod-btn";
    toRec.innerHTML = "红笔圈错题<small>打开原卷 · 用红笔直接圈 · 圈完就记下</small>";
    toRec.onclick = () => {
      $("pathNodeOverlay").classList.add("hidden");
      openMarkSheet({
        unitId: node.unitId,
        source: node.type === "exam" ? "exam" : "daily-calc",
      });
    };
    grid.appendChild(toRec);

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

  /* —— 错题录入 —— */
  function clearPendingPhoto() {
    if (state.pendingPhotoUrl) URL.revokeObjectURL(state.pendingPhotoUrl);
    state.pendingPhotoBlob = null;
    state.pendingPhotoUrl = "";
    $("mistakePhoto").value = "";
    $("mistakePhotoPreview").classList.add("hidden");
    $("mistakePhotoClear").hidden = true;
  }

  function refreshItemNos() {
    const unitId = $("mistakeUnit").value;
    const source = $("mistakeSource").value;
    const n = sourceItemCount(unitId, source);
    const host = $("mistakeItemNos");
    host.innerHTML = "";
    for (let i = 1; i <= n; i++) {
      const lab = document.createElement("label");
      lab.innerHTML = '<input type="checkbox" value="' + i + '" /> ' + i;
      host.appendChild(lab);
    }
    host.querySelectorAll("input").forEach((el) => {
      el.addEventListener("change", syncExcerptFromChecks);
    });
    syncExcerptFromChecks();
  }

  function selectedItemNos() {
    return Array.from($("mistakeItemNos").querySelectorAll("input:checked")).map((el) =>
      Number(el.value)
    );
  }

  function syncExcerptFromChecks() {
    const source = $("mistakeSource").value;
    if (source === "exam") return;
    const nos = selectedItemNos();
    const text = excerptFromBank($("mistakeUnit").value, source, nos);
    if (text) $("mistakeText").value = text;
  }

  async function renderRecords() {
    await W.ready();
    const store = P.ensure();
    const mistakes = await W.listMistakes();
    $("recordsScore").innerHTML =
      "连续 <b>" +
      (store.streak.count || 0) +
      "</b> 天 · 错题 <b>" +
      mistakes.length +
      "</b> 条<br/><span style='color:var(--muted);font-size:.88rem'>原卷上红笔圈题即可入库</span>";

    const actions = $("recordsActions");
    actions.innerHTML = "";
    DATA.units.forEach((u) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "rec-card";
      b.innerHTML =
        "<strong>" + u.name + "</strong><br/><small style='color:var(--muted)'>空白错题重练纸 · PDF</small>";
      b.onclick = () => openPdf(u.wrongPdf);
      actions.appendChild(b);
    });

    const sel = $("mistakeUnit");
    const prevUnit = sel.value;
    sel.innerHTML = DATA.units
      .map((u) => '<option value="' + u.id + '">' + u.name + "</option>")
      .join("");
    if (prevUnit && DATA.units.some((u) => u.id === prevUnit)) sel.value = prevUnit;
    else {
      const cur = P.currentNode();
      if (cur) sel.value = cur.unitId;
    }
    refreshItemNos();

    const list = $("recordsList");
    $("recordsMeta").textContent = "我的错题（" + mistakes.length + "）";
    state.objectUrls.forEach((u) => URL.revokeObjectURL(u));
    state.objectUrls = [];

    if (!mistakes.length) {
      list.innerHTML =
        '<p class="meta" style="padding:8px 0">还没有错题。打印练习 → 红笔批改 → 上方「红笔圈错题」在原卷上圈出来。</p>';
      return;
    }

    list.innerHTML = "";
    for (const m of mistakes) {
      const div = document.createElement("div");
      div.className = "mistake-item";
      const nos = (m.itemNos || []).join("、") || "—";
      let thumbHtml =
        '<div class="thumb is-empty" aria-hidden="true">暂无<br/>照片</div>';
      if (m.photoId) {
        try {
          const url = await W.getPhotoUrl(m.photoId);
          if (url) {
            state.objectUrls.push(url);
            thumbHtml = '<img class="thumb" src="' + url + '" alt="批改缩略图" />';
          }
        } catch (e) {
          /* ignore */
        }
      }
      div.innerHTML =
        '<div class="row">' +
        thumbHtml +
        "<div style='flex:1;min-width:0'><span class='kind'>" +
        escapeHtml(m.kind || "") +
        " · " +
        escapeHtml(m.unitTitle || "") +
        " · " +
        escapeHtml(SOURCE_LABEL[m.source] || m.source || "") +
        " · 题 " +
        escapeHtml(nos) +
        " · " +
        escapeHtml(m.at || "") +
        "</span><p style='margin:6px 0 0;font-weight:700;white-space:pre-wrap'>" +
        escapeHtml(m.text || "（无摘录）") +
        "</p>" +
        (m.note
          ? "<p style='margin:4px 0 0;color:var(--muted);font-size:.88rem'>订正：" +
            escapeHtml(m.note) +
            "</p>"
          : "") +
        '<div class="ops">' +
        '<button type="button" data-act="photo" data-id="' +
        m.id +
        '">' +
        (m.photoId ? "看原图" : "补拍照片") +
        "</button>" +
        '<button type="button" data-act="orig" data-id="' +
        m.id +
        '">重练原题</button>' +
        '<button type="button" data-act="similar" data-id="' +
        m.id +
        '">练类似题</button>' +
        '<button type="button" class="del" data-act="del" data-id="' +
        m.id +
        '">删除</button>' +
        "</div></div></div>";
      list.appendChild(div);
    }

    list.querySelectorAll("[data-act]").forEach((btn) => {
      btn.onclick = () => onMistakeAction(btn.getAttribute("data-act"), btn.getAttribute("data-id"));
    });
  }

  async function onMistakeAction(act, id) {
    if (act === "del") {
      if (!confirm("删除这条错题？")) return;
      await W.removeMistake(id);
      renderRecords();
      return;
    }
    if (act === "photo") {
      openPhotoViewer(id);
      return;
    }
    if (act === "orig") {
      await printOriginalPractice(id);
      return;
    }
    if (act === "similar") {
      await printSimilarPractice(id);
    }
  }

  async function openPhotoViewer(id) {
    state.photoViewId = id;
    const m = await W.getMistake(id);
    const body = $("photoOverlayBody");
    body.innerHTML = "";
    if (m && m.photoId) {
      const url = await W.getPhotoUrl(m.photoId);
      if (url) {
        state.objectUrls.push(url);
        const img = document.createElement("img");
        img.src = url;
        img.alt = "批改照片";
        body.appendChild(img);
      } else {
        body.innerHTML = "<p class='meta'>暂无照片，可用下方按钮补拍。</p>";
      }
    } else {
      body.innerHTML = "<p class='meta'>暂无照片，可用下方按钮补拍。</p>";
    }
    $("photoOverlay").classList.remove("hidden");
  }

  async function submitMistake(e) {
    e.preventDefault();
    const unit = P.unitById($("mistakeUnit").value);
    const source = $("mistakeSource").value;
    const itemNos = selectedItemNos();
    if (!itemNos.length) {
      alert("请至少勾选一道错题题号");
      return;
    }
    let text = ($("mistakeText").value || "").trim();
    if (!text && source !== "exam") {
      text = excerptFromBank(unit.id, source, itemNos);
    }
    if (!text && source === "exam") {
      text = "考前测试 · 题号 " + itemNos.join("、") + "（可稍后补摘录）";
    }
    if (!text) {
      alert("请填写题干摘录");
      return;
    }

    let photoId = "";
    if (state.pendingPhotoBlob) {
      photoId = await W.savePhotoBlob(state.pendingPhotoBlob);
    }

    await W.putMistake({
      unitId: unit.id,
      unitTitle: unit.name,
      source: source,
      kind: $("mistakeKind").value,
      itemNos: itemNos,
      text: text,
      note: ($("mistakeNote").value || "").trim(),
      photoId: photoId,
    });

    $("mistakeNote").value = "";
    $("mistakeText").value = "";
    clearPendingPhoto();
    $("mistakeItemNos").querySelectorAll("input").forEach((el) => {
      el.checked = false;
    });
    renderRecords();
  }

  async function exportMistakes() {
    const rows = await W.exportMeta(false);
    const blob = new Blob([JSON.stringify({ exportedAt: new Date().toISOString(), mistakes: rows }, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "math-desk-错题备份.json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /* —— A4 组卷 / 错题练习 —— */
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
        /* keep figure only */
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

  function sheetShell(unitTitle, body, meta, pageIndex, pageTotal, kindTitle) {
    return (
      '<article class="sheet-a4' +
      (pageIndex > 0 ? " page-break" : "") +
      '"><header class="sheet-head"><p class="sheet-brand">数学书桌 · Math Desk</p><p class="sheet-title">' +
      escapeHtml(unitTitle) +
      " · " +
      escapeHtml(kindTitle || "日常练习") +
      '</p><p class="sheet-meta">' +
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

  async function printOriginalPractice(id) {
    const m = await W.getMistake(id);
    if (!m) return;
    let photoBlock = "";
    if (m.photoId) {
      try {
        const url = await W.getPhotoUrl(m.photoId);
        if (url) {
          state.objectUrls.push(url);
          photoBlock =
            '<div class="block"><h3>批改照片（对照）</h3><div class="q-fig"><img src="' +
            url +
            '" alt="批改照片" style="width:88%;max-width:100%;height:auto" /></div></div>';
        }
      } catch (e) {
        /* ignore */
      }
    }
    const lines = String(m.text || "")
      .split(/\n+/)
      .filter(Boolean)
      .map((t, i) => itemHtml(i + 1 + ". " + t.replace(/^\d+\.\s*/, "")))
      .join("");
    const body =
      '<div class="block"><h3>错题原题 · 订正</h3><p class="sub">' +
      escapeHtml(SOURCE_LABEL[m.source] || "") +
      " · " +
      escapeHtml(m.kind || "") +
      " · 题号 " +
      escapeHtml((m.itemNos || []).join("、") || "—") +
      (m.note ? " · 要点：" + escapeHtml(m.note) : "") +
      '</p><ol class="q">' +
      (lines || itemHtml(m.text || "（无摘录）")) +
      "</ol></div>" +
      photoBlock;
    $("printRoot").innerHTML = sheetShell(m.unitTitle || "错题", body, "原题订正纸 · 可对照照片", 0, 1, "错题订正");
    $("btnDownload").disabled = false;
    window.print();
  }

  function pickSimilarItems(unitId, source, excludeNos, want) {
    want = want || 4;
    const track = trackFromSource(source) || "calc";
    const bank = dailyBank(unitId);
    const exclude = new Set((excludeNos || []).map(Number));
    const picked = [];

    function takeFrom(sectionKey) {
      const section = bank[sectionKey];
      if (!section || !section.items) return;
      section.items.forEach((raw, idx) => {
        const no = idx + 1;
        if (sectionKey === track && exclude.has(no)) return;
        if (picked.length >= want) return;
        picked.push({ sectionKey: sectionKey, raw: raw });
      });
    }

    takeFrom(track);
    if (picked.length < want) {
      ["calc", "key", "app"].forEach((k) => {
        if (k !== track) takeFrom(k);
      });
    }
    return picked.slice(0, want);
  }

  async function printSimilarPractice(id) {
    const m = await W.getMistake(id);
    if (!m) return;
    if (m.source === "exam") {
      /* 考前无结构化题库：用该单元日常三线变式 */
      const bank = dailyBank(m.unitId);
      const body = ["calc", "key", "app"]
        .map((k) => bank[k])
        .filter(Boolean)
        .map((s) => blockHtml(s, true))
        .join("");
      $("printRoot").innerHTML = sheetShell(
        bank.title,
        body,
        "考前错题 · 同单元日常变式（非原卷原题）",
        0,
        1,
        "类似题练习"
      );
      $("btnDownload").disabled = false;
      window.print();
      return;
    }

    const picked = pickSimilarItems(m.unitId, m.source, m.itemNos, 5);
    if (!picked.length) {
      alert("该单元暂无可用变式题");
      return;
    }
    const lis = picked.map((p) => itemHtml(p.raw)).join("");
    const track = trackFromSource(m.source);
    const bank = dailyBank(m.unitId);
    const title = (bank[track] && bank[track].title) || "类似题";
    const body =
      '<div class="block"><h3>' +
      escapeHtml(title) +
      ' · 类似题</h3><p class="sub">同单元变式 · 避开已错题号 ' +
      escapeHtml((m.itemNos || []).join("、") || "—") +
      ' · 约 15 分钟</p><ol class="q">' +
      lis +
      "</ol></div>";
    $("printRoot").innerHTML = sheetShell(bank.title, body, "错题库 · 类似题型练习", 0, 1, "类似题练习");
    $("btnDownload").disabled = false;
    window.print();
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

  $("btnOpenMark").onclick = () => openMarkSheet({});
  $("markClose").onclick = () => $("markOverlay").classList.add("hidden");
  $("markUnit").onchange = () => loadMarkPages();
  $("markSource").onchange = () => loadMarkPages();
  $("markPrevPage").onclick = () => {
    if (state.mark.pageIndex <= 0) return;
    state.mark.pageIndex -= 1;
    showMarkPage();
  };
  $("markNextPage").onclick = () => {
    if (state.mark.pageIndex >= state.mark.pages.length - 1) return;
    state.mark.pageIndex += 1;
    showMarkPage();
  };
  $("markUndo").onclick = undoMarkStroke;
  $("markClear").onclick = clearMarkInk;
  $("markSave").onclick = () => {
    saveMarkSheet().catch((err) => {
      console.error(err);
      alert("记下失败，请重试");
    });
  };
  $("markPhoto").onchange = async () => {
    const file = $("markPhoto").files && $("markPhoto").files[0];
    if (!file) return;
    try {
      const blob = await W.compressImage(file);
      const img = await loadImageFromBlob(blob);
      state.mark.pages = [img];
      state.mark.pageIndex = 0;
      state.mark.strokes = [[]];
      state.mark.ready = true;
      showMarkPage();
    } catch (err) {
      alert("照片打不开，请换一张再试");
    }
  };

  $("mistakeUnit").onchange = refreshItemNos;
  $("mistakeSource").onchange = refreshItemNos;
  $("mistakeForm").onsubmit = (e) => {
    submitMistake(e).catch((err) => {
      console.error(err);
      alert("入库失败，请重试");
    });
  };
  $("btnExportMistakes").onclick = () => {
    exportMistakes().catch(() => alert("导出失败"));
  };
  $("mistakePhotoClear").onclick = clearPendingPhoto;
  $("mistakePhoto").onchange = async () => {
    const file = $("mistakePhoto").files && $("mistakePhoto").files[0];
    if (!file) return;
    try {
      const blob = await W.compressImage(file);
      clearPendingPhoto();
      state.pendingPhotoBlob = blob;
      state.pendingPhotoUrl = URL.createObjectURL(blob);
      $("mistakePhotoImg").src = state.pendingPhotoUrl;
      $("mistakePhotoPreview").classList.remove("hidden");
      $("mistakePhotoClear").hidden = false;
    } catch (err) {
      alert("图片处理失败，可先不拍、只勾题号入库");
    }
  };

  $("photoOverlayClose").onclick = () => $("photoOverlay").classList.add("hidden");
  $("photoReplaceInput").onchange = async () => {
    const file = $("photoReplaceInput").files && $("photoReplaceInput").files[0];
    if (!file || !state.photoViewId) return;
    try {
      const m = await W.getMistake(state.photoViewId);
      if (!m) return;
      const blob = await W.compressImage(file);
      if (m.photoId) await W.deletePhoto(m.photoId);
      const photoId = await W.savePhotoBlob(blob);
      await W.updateMistake(m.id, { photoId: photoId });
      $("photoReplaceInput").value = "";
      await openPhotoViewer(m.id);
      renderRecords();
    } catch (err) {
      alert("补拍失败，请重试");
    }
  };

  if ($("practiceClose")) {
    $("practiceClose").onclick = () => $("practiceOverlay").classList.add("hidden");
  }

  W.ready()
    .then(() => showView("home"))
    .catch(() => showView("home"));
})();
