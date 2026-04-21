import { api } from "./api.js";
import { loadCategories } from "./home.js";
import { escapeHtml, setStatus } from "./util.js";

export async function initSettings() {
  // Load current settings
  try {
    const settings = await api.getSettings();
    document.getElementById("setting-source-lang").value = settings.source_lang;
    document.getElementById("setting-target-lang").value = settings.target_lang;
    if (settings.tts_voice) {
      // Will be selected after voices are loaded
      document.getElementById("setting-tts-voice").dataset.pending = settings.tts_voice;
    }
  } catch (e) {
    setStatus(document.getElementById("settings-status"), e.message, "error");
  }

  document.getElementById("btn-save-settings").addEventListener("click", saveSettings);
  document.getElementById("btn-load-voices").addEventListener("click", loadVoices);
  document.getElementById("btn-test-providers").addEventListener("click", testProviders);

  // Categories management
  document.getElementById("btn-add-cat").addEventListener("click", addCategory);
  await loadCategoriesList();

  // Backup & Restore
  document.getElementById("btn-backup-db").addEventListener("click", backupDatabase);
  document.getElementById("btn-restore-db").addEventListener("click", restoreDatabase);
}

async function saveSettings() {
  const status = document.getElementById("settings-status");
  const data = {
    source_lang: document.getElementById("setting-source-lang").value.trim(),
    target_lang: document.getElementById("setting-target-lang").value.trim(),
    tts_voice: document.getElementById("setting-tts-voice").value,
  };

  if (!data.source_lang || !data.target_lang) {
    setStatus(status, "Languages cannot be empty", "error");
    return;
  }

  try {
    await api.updateSettings(data);
    setStatus(status, "Settings saved!", "success");
  } catch (e) {
    setStatus(status, e.message, "error");
  }
}

async function loadVoices() {
  const lang = document.getElementById("setting-target-lang").value.trim();
  if (!lang) return;

  const select = document.getElementById("setting-tts-voice");
  const pending = select.dataset.pending || "";

  try {
    const voices = await api.listVoices(lang);
    select.innerHTML = '<option value="">Default (auto-select)</option>';
    for (const v of voices) {
      const selected = v.id === pending ? "selected" : "";
      select.innerHTML += `<option value="${v.id}" ${selected}>${escapeHtml(v.display_name)} (${v.gender})</option>`;
    }
    delete select.dataset.pending;
  } catch (e) {
    alert(`Could not load voices: ${e.message}`);
  }
}

async function testProviders() {
  const container = document.getElementById("provider-status");
  container.innerHTML = '<p class="status loading">Testing...</p>';

  try {
    const data = await api.healthProviders();
    container.innerHTML = ["translator", "tts", "stt"]
      .map((cap) => {
        const s = data[cap];
        const dot = s.ok ? "ok" : "fail";
        const text = s.ok ? `${cap}: ${s.provider} OK` : `${cap}: ${s.provider} — ${s.error}`;
        return `<div class="provider-row"><span class="dot ${dot}"></span><span>${escapeHtml(text)}</span></div>`;
      })
      .join("");
  } catch (e) {
    container.innerHTML = `<p class="status error">${escapeHtml(e.message)}</p>`;
  }
}

async function addCategory() {
  const input = document.getElementById("new-cat-name");
  const name = input.value.trim();
  if (!name) return;

  try {
    await api.createCategory(name);
    input.value = "";
    await loadCategoriesList();
    await loadCategories();
  } catch (e) {
    alert(e.message);
  }
}

async function loadCategoriesList() {
  const container = document.getElementById("categories-list");
  try {
    const cats = await api.listCategories();
    if (cats.length === 0) {
      container.innerHTML = '<p style="color:#868e96;">No categories yet.</p>';
      return;
    }
    container.innerHTML = cats
      .map(
        (c) => `
            <div class="cat-row" data-id="${c.id}">
                <span class="cat-name">${escapeHtml(c.name)}</span>
                <span class="cat-count">${c.item_count} items</span>
                <button class="small btn-rename-cat" data-id="${c.id}" data-name="${escapeHtml(c.name)}">Rename</button>
                <button class="small danger btn-delete-cat" data-id="${c.id}">Delete</button>
            </div>`,
      )
      .join("");

    container.querySelectorAll(".btn-rename-cat").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const newName = prompt("Rename category:", btn.dataset.name);
        if (newName?.trim()) {
          try {
            await api.updateCategory(parseInt(btn.dataset.id, 10), newName.trim());
            await loadCategoriesList();
            await loadCategories();
          } catch (e) {
            alert(e.message);
          }
        }
      });
    });

    container.querySelectorAll(".btn-delete-cat").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Delete this category? Items will become uncategorized.")) return;
        try {
          await api.deleteCategory(parseInt(btn.dataset.id, 10));
          await loadCategoriesList();
          await loadCategories();
        } catch (e) {
          alert(e.message);
        }
      });
    });
  } catch (e) {
    container.innerHTML = `<p class="status error">${escapeHtml(e.message)}</p>`;
  }
}

function backupDatabase() {
  const status = document.getElementById("backup-status");
  setStatus(status, "Preparing backup...", "loading");

  const a = document.createElement("a");
  a.href = "/api/backup";
  a.click();
  setStatus(status, "Backup download started!", "success");
}

async function restoreDatabase() {
  const fileInput = document.getElementById("restore-file");
  const status = document.getElementById("restore-status");

  if (!fileInput.files || fileInput.files.length === 0) {
    setStatus(status, "Please select a backup file first.", "error");
    return;
  }

  if (
    !confirm(
      "This will replace ALL current data (items, categories, settings) with the backup. A safety copy of the current database will be kept. Continue?",
    )
  ) {
    return;
  }

  setStatus(status, "Restoring...", "loading");

  const form = new FormData();
  form.append("file", fileInput.files[0]);

  try {
    const resp = await fetch("/api/restore", { method: "POST", body: form });
    const data = await resp.json();
    if (!resp.ok) {
      const msg = data?.error?.message || data?.detail?.[0]?.msg || JSON.stringify(data);
      throw new Error(msg);
    }
    setStatus(status, "Database restored! Reloading page...", "success");
    fileInput.value = "";
    setTimeout(() => window.location.reload(), 1000);
  } catch (e) {
    setStatus(status, e.message, "error");
  }
}
