const API = window.location.origin;
let direction = "tr-en";

const $ = (sel) => document.querySelector(sel);
const sourceText = $("#source-text");
const resultText = $("#result-text");
const btnTranslate = $("#btn-translate");
const btnSwap = $("#btn-swap");
const btnCopy = $("#btn-copy");
const btnClearHistory = $("#btn-clear-history");
const charCount = $("#char-count");
const durationEl = $("#duration");
const statusEl = $("#status");
const sourceLang = $("#source-lang");
const targetLang = $("#target-lang");
const historyList = $("#history-list");
const statsEl = $("#stats");

// --- Direction ---
function updateDirection() {
    if (direction === "tr-en") {
        sourceLang.textContent = "Türkçe";
        targetLang.textContent = "İngilizce";
    } else {
        sourceLang.textContent = "İngilizce";
        targetLang.textContent = "Türkçe";
    }
}

btnSwap.addEventListener("click", () => {
    direction = direction === "tr-en" ? "en-tr" : "tr-en";
    updateDirection();
    // Swap texts if there's content
    const src = sourceText.value;
    const res = resultText.textContent;
    if (res) {
        sourceText.value = res;
        resultText.textContent = src;
    }
});

// --- Char count ---
sourceText.addEventListener("input", () => {
    charCount.textContent = `${sourceText.value.length} karakter`;
});

// --- Translate ---
async function translate() {
    const text = sourceText.value.trim();
    if (!text) return;

    btnTranslate.disabled = true;
    btnTranslate.textContent = "Çevriliyor...";
    resultText.textContent = "";
    durationEl.textContent = "";

    try {
        const res = await fetch(`${API}/translate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, direction }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        resultText.textContent = data.translation;
        durationEl.textContent = `${data.duration_ms} ms`;
        addHistory(text, data.translation, direction);
    } catch (err) {
        resultText.textContent = `Hata: ${err.message}`;
    } finally {
        btnTranslate.disabled = false;
        btnTranslate.textContent = "Çevir";
    }
}

btnTranslate.addEventListener("click", translate);

// Ctrl+Enter shortcut
sourceText.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "Enter") translate();
});

// --- Copy ---
btnCopy.addEventListener("click", () => {
    const text = resultText.textContent;
    if (text) navigator.clipboard.writeText(text);
});

// --- History (localStorage) ---
function getHistory() {
    try { return JSON.parse(localStorage.getItem("opus_history") || "[]"); }
    catch { return []; }
}

function saveHistory(items) {
    localStorage.setItem("opus_history", JSON.stringify(items.slice(0, 50)));
}

function addHistory(source, result, dir) {
    const items = getHistory();
    items.unshift({ source, result, dir, ts: Date.now() });
    saveHistory(items);
    renderHistory();
}

function renderHistory() {
    const items = getHistory();
    historyList.innerHTML = "";
    if (!items.length) {
        historyList.innerHTML = '<div style="color:var(--text-dim);font-size:0.85rem">Henüz çeviri yok</div>';
        return;
    }
    items.slice(0, 20).forEach((item) => {
        const el = document.createElement("div");
        el.className = "history-item";
        const short = item.source.length > 60 ? item.source.slice(0, 60) + "…" : item.source;
        el.innerHTML = `<span>${short} → ${item.result.slice(0, 40)}</span><span class="dir">${item.dir.toUpperCase()}</span>`;
        el.addEventListener("click", () => {
            direction = item.dir;
            updateDirection();
            sourceText.value = item.source;
            resultText.textContent = item.result;
        });
        historyList.appendChild(el);
    });
}

btnClearHistory.addEventListener("click", () => {
    localStorage.removeItem("opus_history");
    renderHistory();
});

// --- Health / Stats ---
async function fetchHealth() {
    try {
        const res = await fetch(`${API}/health`);
        const data = await res.json();
        statusEl.textContent = "Çevrimiçi";
        statusEl.className = "status online";

        const upH = Math.floor(data.uptime / 3600);
        const upM = Math.floor((data.uptime % 3600) / 60);

        let cards = `
            <div class="stat-card"><div class="label">Cihaz</div><div class="value">${data.device.toUpperCase()}</div></div>
            <div class="stat-card"><div class="label">Toplam Çeviri</div><div class="value">${data.total_translations}</div></div>
            <div class="stat-card"><div class="label">Çalışma Süresi</div><div class="value">${upH}s ${upM}dk</div></div>
            <div class="stat-card"><div class="label">Yüklü Modeller</div><div class="value">${data.models_loaded.length > 0 ? data.models_loaded.join(", ") : "Bekleniyor"}</div></div>
        `;
        if (data.gpu_name) {
            cards += `
                <div class="stat-card"><div class="label">GPU</div><div class="value">${data.gpu_name}</div></div>
                <div class="stat-card"><div class="label">VRAM</div><div class="value">${data.gpu_memory_used} / ${data.gpu_memory_total}</div></div>
            `;
        }
        statsEl.innerHTML = cards;
    } catch {
        statusEl.textContent = "Çevrimdışı";
        statusEl.className = "status";
    }
}

// --- Init ---
updateDirection();
renderHistory();
fetchHealth();
setInterval(fetchHealth, 15000);
