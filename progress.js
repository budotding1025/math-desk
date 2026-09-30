/* 数学书桌 · 进度 / 错题 / 当前单元站 */
(function (g) {
  const KEY = "math-desk-v1";
  const DATA = g.MATH_DESK_DATA;

  function load() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "{}") || {};
    } catch (e) {
      return {};
    }
  }

  function save(store) {
    localStorage.setItem(KEY, JSON.stringify(store));
  }

  function ensure() {
    const s = load();
    if (!s.completed) s.completed = {};
    if (!s.mistakes) s.mistakes = [];
    if (!s.streak) s.streak = { count: 0, last: "" };
    if (!s.currentUnitId) s.currentUnitId = (DATA && DATA.currentUnitId) || "u02";
    if (!s.currentTrack) s.currentTrack = (DATA && DATA.currentTrack) || "daily";
    return s;
  }

  function unitById(id) {
    return (DATA.units || []).find((u) => u.id === id) || DATA.units[0];
  }

  /** 路径节点：每单元 2 站 —— 日常练习、考前测试 */
  function semesterPath() {
    const nodes = [];
    (DATA.units || []).forEach((u) => {
      nodes.push({
        type: "daily",
        id: u.id + "-daily",
        unitId: u.id,
        unitTitle: u.name,
        unitNo: u.no,
        title: "日常练习 · 组卷打印",
        kind: "约 15 分钟 · ①②③ 可选",
        lessonLabel: "第一课",
        unit: u,
      });
      nodes.push({
        type: "exam",
        id: u.id + "-exam",
        unitId: u.id,
        unitTitle: u.name,
        unitNo: u.no,
        title: "考前测试",
        kind: (u.examComplete ? "完整卷" : "部分卷") + " · 30–40 分钟",
        lessonLabel: "第二课",
        unit: u,
      });
    });
    return nodes;
  }

  function currentNode() {
    const s = ensure();
    const path = semesterPath();
    const hit = path.find((n) => n.unitId === s.currentUnitId && n.type === s.currentTrack);
    return hit || path.find((n) => n.unitId === "u02" && n.type === "daily") || path[0];
  }

  function setCurrent(unitId, track) {
    const s = ensure();
    s.currentUnitId = unitId;
    s.currentTrack = track === "exam" ? "exam" : "daily";
    bumpStreak(s);
    save(s);
  }

  function bumpStreak(s) {
    const today = new Date().toISOString().slice(0, 10);
    if (s.streak.last !== today) {
      const y = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
      s.streak.count = s.streak.last === y ? (s.streak.count || 0) + 1 : 1;
      s.streak.last = today;
    }
  }

  function markDone(nodeId) {
    const s = ensure();
    if (!s.completed[nodeId]) s.completed[nodeId] = { count: 0, at: 0 };
    s.completed[nodeId].count += 1;
    s.completed[nodeId].at = Date.now();
    bumpStreak(s);
    save(s);
  }

  function completedCount() {
    const s = ensure();
    return Object.keys(s.completed).filter((k) => s.completed[k].count > 0).length;
  }

  function addMistake(entry) {
    const s = ensure();
    s.mistakes.unshift(
      Object.assign(
        {
          id: "m" + Date.now(),
          at: new Date().toISOString().slice(0, 10),
          unitId: "",
          unitTitle: "",
          kind: "计算错",
          text: "",
          note: "",
        },
        entry
      )
    );
    if (s.mistakes.length > 200) s.mistakes.length = 200;
    save(s);
  }

  function removeMistake(id) {
    const s = ensure();
    s.mistakes = (s.mistakes || []).filter((m) => m.id !== id);
    save(s);
  }

  function listMistakes() {
    return ensure().mistakes || [];
  }

  g.MathProgress = {
    ensure,
    save,
    unitById,
    semesterPath,
    currentNode,
    setCurrent,
    markDone,
    completedCount,
    addMistake,
    removeMistake,
    listMistakes,
  };
})(window);
