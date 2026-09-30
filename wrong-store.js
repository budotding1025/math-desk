/* 数学书桌 · 错题本机后台（IndexedDB）
 * 照片可选：可先勾选题号入库，之后补拍。
 */
(function (g) {
  const DB_NAME = "math-desk-wrong";
  const DB_VER = 1;
  const STORE_META = "mistakes";
  const STORE_PHOTO = "photos";
  const LEGACY_KEY = "math-desk-v1";

  let dbPromise = null;
  let migrated = false;

  function openDb() {
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VER);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(STORE_META)) {
          const s = db.createObjectStore(STORE_META, { keyPath: "id" });
          s.createIndex("byAt", "at", { unique: false });
          s.createIndex("byUnit", "unitId", { unique: false });
        }
        if (!db.objectStoreNames.contains(STORE_PHOTO)) {
          db.createObjectStore(STORE_PHOTO, { keyPath: "id" });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
    return dbPromise;
  }

  function txDone(tx) {
    return new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error || new Error("aborted"));
    });
  }

  function uid(prefix) {
    return (prefix || "m") + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  }

  async function migrateLegacy() {
    if (migrated) return;
    migrated = true;
    try {
      const raw = JSON.parse(localStorage.getItem(LEGACY_KEY) || "{}") || {};
      const legacy = Array.isArray(raw.mistakes) ? raw.mistakes : [];
      if (!legacy.length) return;
      const existing = await listMistakes();
      const ids = new Set(existing.map((m) => m.id));
      for (const m of legacy) {
        if (!m || !m.id || ids.has(m.id)) continue;
        await putMistake({
          id: m.id,
          at: m.at || new Date().toISOString().slice(0, 10),
          unitId: m.unitId || "",
          unitTitle: m.unitTitle || "",
          source: m.source || "exam",
          kind: m.kind || "其他",
          itemNos: m.itemNos || [],
          text: m.text || "",
          note: m.note || "",
          photoId: m.photoId || "",
        });
      }
      raw.mistakes = [];
      localStorage.setItem(LEGACY_KEY, JSON.stringify(raw));
    } catch (e) {
      /* ignore migrate errors */
    }
  }

  async function putMistake(entry) {
    const db = await openDb();
    const row = Object.assign(
      {
        id: uid("m"),
        at: new Date().toISOString().slice(0, 10),
        unitId: "",
        unitTitle: "",
        source: "daily-calc",
        kind: "计算错",
        itemNos: [],
        text: "",
        note: "",
        photoId: "",
      },
      entry
    );
    const tx = db.transaction(STORE_META, "readwrite");
    tx.objectStore(STORE_META).put(row);
    await txDone(tx);
    return row;
  }

  async function updateMistake(id, patch) {
    const db = await openDb();
    const tx = db.transaction(STORE_META, "readwrite");
    const store = tx.objectStore(STORE_META);
    const cur = await new Promise((resolve, reject) => {
      const r = store.get(id);
      r.onsuccess = () => resolve(r.result);
      r.onerror = () => reject(r.error);
    });
    if (!cur) {
      await txDone(tx);
      return null;
    }
    const next = Object.assign({}, cur, patch, { id: cur.id });
    store.put(next);
    await txDone(tx);
    return next;
  }

  async function removeMistake(id) {
    const db = await openDb();
    const tx = db.transaction([STORE_META, STORE_PHOTO], "readwrite");
    const meta = await new Promise((resolve, reject) => {
      const r = tx.objectStore(STORE_META).get(id);
      r.onsuccess = () => resolve(r.result);
      r.onerror = () => reject(r.error);
    });
    tx.objectStore(STORE_META).delete(id);
    if (meta && meta.photoId) {
      tx.objectStore(STORE_PHOTO).delete(meta.photoId);
    }
    await txDone(tx);
  }

  async function listMistakes() {
    const db = await openDb();
    const tx = db.transaction(STORE_META, "readonly");
    const rows = await new Promise((resolve, reject) => {
      const r = tx.objectStore(STORE_META).getAll();
      r.onsuccess = () => resolve(r.result || []);
      r.onerror = () => reject(r.error);
    });
    await txDone(tx);
    rows.sort((a, b) => String(b.at).localeCompare(String(a.at)) || String(b.id).localeCompare(String(a.id)));
    return rows;
  }

  async function getMistake(id) {
    const db = await openDb();
    const tx = db.transaction(STORE_META, "readonly");
    const row = await new Promise((resolve, reject) => {
      const r = tx.objectStore(STORE_META).get(id);
      r.onsuccess = () => resolve(r.result || null);
      r.onerror = () => reject(r.error);
    });
    await txDone(tx);
    return row;
  }

  /** 压缩后存 JPEG blob；返回 photoId */
  async function savePhotoBlob(blob, photoId) {
    const id = photoId || uid("p");
    const db = await openDb();
    const tx = db.transaction(STORE_PHOTO, "readwrite");
    tx.objectStore(STORE_PHOTO).put({ id: id, blob: blob, at: Date.now() });
    await txDone(tx);
    return id;
  }

  async function getPhotoBlob(photoId) {
    if (!photoId) return null;
    const db = await openDb();
    const tx = db.transaction(STORE_PHOTO, "readonly");
    const row = await new Promise((resolve, reject) => {
      const r = tx.objectStore(STORE_PHOTO).get(photoId);
      r.onsuccess = () => resolve(r.result || null);
      r.onerror = () => reject(r.error);
    });
    await txDone(tx);
    return row ? row.blob : null;
  }

  async function getPhotoUrl(photoId) {
    const blob = await getPhotoBlob(photoId);
    if (!blob) return "";
    return URL.createObjectURL(blob);
  }

  async function deletePhoto(photoId) {
    if (!photoId) return;
    const db = await openDb();
    const tx = db.transaction(STORE_PHOTO, "readwrite");
    tx.objectStore(STORE_PHOTO).delete(photoId);
    await txDone(tx);
  }

  /** 将 File/Blob 压成较小 JPEG（最长边 maxEdge） */
  function compressImage(file, maxEdge, quality) {
    maxEdge = maxEdge || 1600;
    quality = quality || 0.72;
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        let w = img.naturalWidth || img.width;
        let h = img.naturalHeight || img.height;
        const scale = Math.min(1, maxEdge / Math.max(w, h));
        w = Math.max(1, Math.round(w * scale));
        h = Math.max(1, Math.round(h * scale));
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#fff";
        ctx.fillRect(0, 0, w, h);
        ctx.drawImage(img, 0, 0, w, h);
        URL.revokeObjectURL(url);
        canvas.toBlob(
          (blob) => {
            if (!blob) reject(new Error("compress failed"));
            else resolve(blob);
          },
          "image/jpeg",
          quality
        );
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("image load failed"));
      };
      img.src = url;
    });
  }

  /** 导出元数据（默认不含大图；可选附带缩略图 dataURL） */
  async function exportMeta(withThumbs) {
    await migrateLegacy();
    const list = await listMistakes();
    const out = [];
    for (const m of list) {
      const row = Object.assign({}, m);
      if (withThumbs && m.photoId) {
        try {
          const blob = await getPhotoBlob(m.photoId);
          if (blob) {
            const small = await compressImage(blob, 320, 0.55);
            row.thumbDataUrl = await new Promise((resolve, reject) => {
              const fr = new FileReader();
              fr.onload = () => resolve(fr.result);
              fr.onerror = () => reject(fr.error);
              fr.readAsDataURL(small);
            });
          }
        } catch (e) {
          /* skip thumb */
        }
      }
      out.push(row);
    }
    return out;
  }

  async function ready() {
    await openDb();
    await migrateLegacy();
  }

  g.WrongStore = {
    ready,
    putMistake,
    updateMistake,
    removeMistake,
    listMistakes,
    getMistake,
    savePhotoBlob,
    getPhotoBlob,
    getPhotoUrl,
    deletePhoto,
    compressImage,
    exportMeta,
    uid,
  };
})(window);
