(function () {
  const units = window.MATH_DAILY || [];
  const unitSelect = document.getElementById("unitSelect");
  const hint = document.getElementById("selectHint");
  const printRoot = document.getElementById("printRoot");
  const btnBuild = document.getElementById("btnBuild");
  const btnPrint = document.getElementById("btnPrint");
  const btnDownload = document.getElementById("btnDownload");

  const examFiles = {
    u01: ["U1 大数的认识（完整）", "printables/u01/04-考前测试/U1_四上_第一单元_大数的认识.pdf"],
    u02: ["U2 角的度量（完整）", "printables/u02/04-考前测试/U2_四上_第二单元_角的度量.pdf"],
    u03: ["U3 三位数乘两位数（部分）", "printables/u03/04-考前测试/U3_四上_第三单元_三位数乘两位数_部分.pdf"],
    u04: ["U4 数量关系（部分）", "printables/u04/04-考前测试/U4_四上_第四单元_数量关系_部分.pdf"],
    u05: ["U5 平行四边形和梯形（部分）", "printables/u05/04-考前测试/U5_四上_第五单元_平行四边形和梯形_部分.pdf"],
  };

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
      hint.textContent = "请至少选择一项";
      return;
    }
    if (n === 1 || layoutMode() === "combine") {
      hint.textContent = "已选 " + n + " 项 · 合订 1 页 A4 · 合计约 15 分钟";
    } else {
      hint.textContent = "已选 " + n + " 项 · 分项 " + n + " 页 A4 · 每页约 15 分钟";
    }
  }

  function fillUnitSelect() {
    unitSelect.innerHTML = units
      .map((u, i) => '<option value="' + u.id + '"' + (i === 0 ? " selected" : "") + ">" + u.title + "</option>")
      .join("");
  }

  function currentUnit() {
    return units.find((u) => u.id === unitSelect.value) || units[0];
  }

  function trimItems(items, max) {
    return (items || []).slice(0, max);
  }

  function blockHtml(section, compact) {
    const max = compact ? 4 : 6;
    const lis = trimItems(section.items, max)
      .map((t) => "<li>" + t + "</li>")
      .join("");
    return (
      '<div class="block">' +
      "<h3>" +
      section.title +
      (compact ? "（精选）" : "") +
      "</h3>" +
      '<p class="sub">' +
      (section.hint || "") +
      "</p>" +
      '<ol class="q">' +
      lis +
      "</ol></div>"
    );
  }

  function sheetShell(unit, bodyInner, metaLine, pageIndex, pageTotal) {
    return (
      '<article class="sheet-a4' +
      (pageIndex > 0 ? " page-break" : "") +
      '">' +
      '<header class="sheet-head">' +
      '<p class="sheet-brand">数学书桌 · Math Desk</p>' +
      '<p class="sheet-title">' +
      unit.title +
      " · 日常练习</p>" +
      '<p class="sheet-meta">' +
      metaLine +
      "　|　第 " +
      (pageIndex + 1) +
      " / " +
      pageTotal +
      " 页</p>" +
      "</header>" +
      '<p class="sheet-info">姓名：________　日期：________　完成：____　正确：____</p>' +
      bodyInner +
      '<p class="sub">订正区：________________________________________________</p>' +
      "</article>"
    );
  }

  function build() {
    const tracks = selectedTracks();
    if (!tracks.length) {
      alert("请至少选择 ① / ② / ③ 中的一项");
      return;
    }
    const unit = currentUnit();
    const sections = tracks.map((k) => unit[k]).filter(Boolean);
    const mode = layoutMode();
    let html = "";

    if (mode === "combine" || sections.length === 1) {
      const compact = sections.length > 1;
      const body = sections.map((s) => blockHtml(s, compact)).join("");
      const names = sections.map((s) => s.title.replace(/^① |^② |^③ /, "")).join(" + ");
      const meta =
        "合订一张　|　已选：" +
        names +
        "　|　番茄钟约 15 分钟";
      html = sheetShell(unit, body, meta, 0, 1);
    } else {
      html = sections
        .map((s, i) =>
          sheetShell(
            unit,
            blockHtml(s, false),
            "分项分页　|　本页：" + s.title + "　|　约 15 分钟",
            i,
            sections.length
          )
        )
        .join("");
    }

    printRoot.innerHTML = html;
    btnPrint.disabled = false;
    btnDownload.disabled = false;
    printRoot.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function downloadHtml() {
    const unit = currentUnit();
    const html =
      "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"UTF-8\" /><title>" +
      unit.title +
      " · 日常练习</title><link rel=\"stylesheet\" href=\"theme.css\" /></head><body>" +
      printRoot.innerHTML +
      "<script>window.onload=function(){window.print()}<\/script></body></html>";
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = unit.id + "-日常练习-A4.html";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function fillExamWrong() {
    const exam = document.getElementById("examList");
    const wrong = document.getElementById("wrongList");
    exam.innerHTML = Object.keys(examFiles)
      .map((id) => {
        const [label, href] = examFiles[id];
        return (
          '<a href="' +
          href +
          '" target="_blank" rel="noopener"><span class="name">' +
          label +
          '</span><span class="meta">30–40 分钟 · PDF</span></a>'
        );
      })
      .join("");
    wrong.innerHTML = units
      .map(
        (u) =>
          '<a href="printables/' +
          u.id +
          "/05-错题库/" +
          u.id +
          '-错题重练-模板.pdf" target="_blank" rel="noopener"><span class="name">' +
          u.title +
          ' · 错题重练</span><span class="meta">PDF</span></a>'
      )
      .join("");
  }

  fillUnitSelect();
  fillExamWrong();
  updateHint();
  document.querySelectorAll("#trackChecks input, #layoutMode input").forEach((el) => {
    el.addEventListener("change", updateHint);
  });
  btnBuild.addEventListener("click", build);
  btnPrint.addEventListener("click", () => window.print());
  btnDownload.addEventListener("click", downloadHtml);
})();
