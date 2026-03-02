"use strict";

const API = window.location.origin;

// ── State ──────────────────────────────────────────────────────────────────
let direction = "tr-en";

// ── DOM helpers ────────────────────────────────────────────────────────────
const el = (id) => document.getElementById(id);
const $ = (sel) => document.querySelector(sel);

// ── API Key ────────────────────────────────────────────────────────────────
const ApiKey = {
    get: () => localStorage.getItem("opus_api_key") || "",
    set: (k) => localStorage.setItem("opus_api_key", k),
    clear: () => localStorage.removeItem("opus_api_key"),
    headers: () => {
        const key = ApiKey.get();
        return key ? { "Content-Type": "application/json", "Authorization": `Bearer ${key}` }
                   : { "Content-Type": "application/json" };
    },
};

// ── Modal ──────────────────────────────────────────────────────────────────
const Modal = {
    show(showError = false) {
        el("key-modal").classList.remove("hidden");
        el("key-error").classList.toggle("hidden", !showError);
        el("key-input").value = "";
        el("key-input").focus();
    },
    hide() { el("key-modal").classList.add("hidden"); },
};

el("key-submit").addEventListener("click", () => {
    const key = el("key-input").value.trim();
    if (!key) return;
    ApiKey.set(key);
    Modal.hide();
    fetchHealth();
});

el("key-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") el("key-submit").click();
});

el("btn-key").addEventListener("click", () => Modal.show());

// ── Fetch wrapper (401 → modal) ────────────────────────────────────────────
async function apiFetch(path, options = {}) {
    const res = await fetch(`${API}${path}`, {
        ...options,
        headers: { ...ApiKey.headers(), ...(options.headers || {}) },
    });
    if (res.status === 401) {
        Modal.show(ApiKey.get() !== ""); // show error only if key was set
        throw new Error("Unauthorized");
    }
    return res;
}

// ── Direction ──────────────────────────────────────────────────────────────
function setDirection(dir) {
    direction = dir;
    el("source-lang").textContent = dir === "tr-en" ? "Türkçe" : "İngilizce";
    el("target-lang").textContent = dir === "tr-en" ? "İngilizce" : "Türkçe";
}

el("btn-swap").addEventListener("click", () => {
    const src = el("source-text").value;
    const res = el("result-text").textContent;
    setDirection(direction === "tr-en" ? "en-tr" : "tr-en");
    if (res) { el("source-text").value = res; el("result-text").textContent = src; }
});

// ── Translate ──────────────────────────────────────────────────────────────
el("source-text").addEventListener("input", () => {
    el("char-count").textContent = `${el("source-text").value.length} karakter`;
});

el("source-text").addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "Enter") doTranslate();
});

el("btn-translate").addEventListener("click", doTranslate);

async function doTranslate() {
    const text = el("source-text").value.trim();
    if (!text) return;

    const btn = el("btn-translate");
    btn.disabled = true;
    btn.textContent = "Çevriliyor...";
    el("result-text").textContent = "";
    el("duration").textContent = "";

    try {
        const res = await apiFetch("/translate", {
            method: "POST",
            body: JSON.stringify({ text, direction }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        el("result-text").textContent = data.translation;
        el("duration").textContent = `${data.duration_ms} ms`;
        History.add(text, data.translation, direction);
    } catch (err) {
        if (err.message !== "Unauthorized")
            el("result-text").textContent = `Hata: ${err.message}`;
    } finally {
        btn.disabled = false;
        btn.textContent = "Çevir";
    }
}

el("btn-copy").addEventListener("click", () => {
    const text = el("result-text").textContent;
    if (text) navigator.clipboard.writeText(text);
});

// ── History ────────────────────────────────────────────────────────────────
const History = {
    get: () => { try { return JSON.parse(localStorage.getItem("opus_history") || "[]"); } catch { return []; } },
    save: (items) => localStorage.setItem("opus_history", JSON.stringify(items.slice(0, 50))),
    add(source, result, dir) {
        const items = this.get();
        items.unshift({ source, result, dir });
        this.save(items);
        this.render();
    },
    render() {
        const list = el("history-list");
        const items = this.get();
        if (!items.length) {
            list.innerHTML = '<div style="color:var(--text-dim);font-size:0.85rem">Henüz çeviri yok</div>';
            return;
        }
        list.innerHTML = "";
        items.slice(0, 20).forEach((item) => {
            const div = document.createElement("div");
            div.className = "history-item";
            const short = item.source.length > 60 ? item.source.slice(0, 60) + "…" : item.source;
            div.innerHTML = `<span>${short} → ${item.result.slice(0, 40)}</span><span class="dir">${item.dir.toUpperCase()}</span>`;
            div.addEventListener("click", () => {
                setDirection(item.dir);
                el("source-text").value = item.source;
                el("result-text").textContent = item.result;
            });
            list.appendChild(div);
        });
    },
};

el("btn-clear-history").addEventListener("click", () => {
    localStorage.removeItem("opus_history");
    History.render();
});

// ── Device toggle ──────────────────────────────────────────────────────────
document.querySelectorAll(".dev-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
        const dev = btn.dataset.dev;
        try {
            const res = await apiFetch("/config/device", {
                method: "POST",
                body: JSON.stringify({ device: dev }),
            });
            if (res.ok) {
                fetchHealth();
            } else {
                const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
                showToast(err.detail || "Cihaz değiştirilemedi", "error");
            }
        } catch (e) {
            if (e.message !== "Unauthorized") showToast(e.message, "error");
        }
    });
});

function syncDeviceToggle(device) {
    const toggle = el("device-toggle");
    toggle.classList.remove("hidden");
    toggle.querySelectorAll(".dev-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.dev === device);
    });
}

// ── Model cards ────────────────────────────────────────────────────────────
document.querySelectorAll(".btn-load").forEach((btn) => {
    btn.addEventListener("click", () => modelAction(btn.dataset.dir, "load"));
});
document.querySelectorAll(".btn-unload").forEach((btn) => {
    btn.addEventListener("click", () => modelAction(btn.dataset.dir, "unload"));
});

async function modelAction(dir, action) {
    const card      = el(`card-${dir}`);
    const loadBtn   = card.querySelector(".btn-load");
    const unloadBtn = card.querySelector(".btn-unload");
    const badge     = el(`badge-${dir}`);

    // Loading state
    if (action === "load") {
        loadBtn.disabled = true;
        loadBtn.textContent = "Yükleniyor…";
        badge.textContent = "Yükleniyor";
        badge.className = "badge loading";
    } else {
        unloadBtn.disabled = true;
        unloadBtn.textContent = "Boşaltılıyor…";
    }

    try {
        const method = action === "load" ? "POST" : "DELETE";
        const path   = action === "load" ? `/models/${dir}/load` : `/models/${dir}`;
        const res = await apiFetch(path, { method });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
            showToast(err.detail || "İşlem başarısız", "error");
        }
    } catch (e) {
        if (e.message !== "Unauthorized") showToast(e.message, "error");
    } finally {
        loadBtn.disabled = false;
        loadBtn.textContent = "Yükle";
        unloadBtn.disabled = false;
        unloadBtn.textContent = "Boşalt";
        await fetchHealth();
    }
}

function syncModelCards(loadedModels) {
    ["tr-en", "en-tr"].forEach((dir) => {
        const loaded = loadedModels.includes(dir);
        const badge  = el(`badge-${dir}`);
        const card   = el(`card-${dir}`);
        const loadBtn   = card.querySelector(".btn-load");
        const unloadBtn = card.querySelector(".btn-unload");

        badge.textContent = loaded ? "Yüklü" : "Boşta";
        badge.className = loaded ? "badge loaded" : "badge";
        card.classList.toggle("loaded", loaded);
        loadBtn.classList.toggle("hidden", loaded);
        unloadBtn.classList.toggle("hidden", !loaded);
    });
}

// ── Health ─────────────────────────────────────────────────────────────────
async function fetchHealth() {
    try {
        const res = await fetch(`${API}/health`); // health herkese açık
        if (!res.ok) throw new Error();
        const data = await res.json();

        el("status").textContent = "Çevrimiçi";
        el("status").className = "status online";

        syncDeviceToggle(data.device);
        syncModelCards(data.models_loaded);

        const upH = Math.floor(data.uptime / 3600);
        const upM = Math.floor((data.uptime % 3600) / 60);

        let html = `
            <div class="stat-card"><div class="label">Cihaz</div><div class="value">${data.device.toUpperCase()}</div></div>
            <div class="stat-card"><div class="label">Toplam Çeviri</div><div class="value">${data.total_translations}</div></div>
            <div class="stat-card"><div class="label">Çalışma Süresi</div><div class="value">${upH}s ${upM}dk</div></div>
            <div class="stat-card"><div class="label">Yüklü Modeller</div><div class="value">${data.models_loaded.length || "—"}</div></div>
        `;
        if (data.cuda_available && data.device !== "cuda") {
            html += `<div class="stat-card"><div class="label">CUDA</div><div class="value">Mevcut</div></div>`;
        }
        if (data.gpu_name) {
            html += `
                <div class="stat-card"><div class="label">GPU</div><div class="value" style="font-size:0.9rem">${data.gpu_name}</div></div>
                <div class="stat-card"><div class="label">VRAM</div><div class="value">${data.gpu_memory_used} / ${data.gpu_memory_total}</div></div>
            `;
        }
        el("stats").innerHTML = html;

        // API key kontrolü — server key gerektiriyorsa ve localStorage'da yoksa modal aç
        if (!ApiKey.get()) {
            const testRes = await fetch(`${API}/detect?text=test`);
            if (testRes.status === 401) Modal.show();
        }
    } catch {
        el("status").textContent = "Çevrimdışı";
        el("status").className = "status";
    }
}

// ── Toast bildirimi ────────────────────────────────────────────────────────
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("toast-visible"));
    setTimeout(() => {
        toast.classList.remove("toast-visible");
        toast.addEventListener("transitionend", () => toast.remove());
    }, 3500);
}

// ── Init ───────────────────────────────────────────────────────────────────
setDirection("tr-en");
History.render();
fetchHealth();
setInterval(fetchHealth, 15000);
