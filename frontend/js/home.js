import { api } from "./api.js";
import { debounce, escapeHtml, setStatus } from "./util.js";

let allCategories = [];

export async function initHome() {
  await loadCategories();
  await loadItems();

  document.getElementById("btn-translate").addEventListener("click", addItem);
  document.getElementById("home-search").addEventListener(
    "input",
    debounce(() => loadItems()),
  );
  document.getElementById("home-category-filter").addEventListener("change", () => loadItems());

  // Edit modal
  document.getElementById("btn-edit-save").addEventListener("click", saveEdit);
  document.getElementById("btn-edit-cancel").addEventListener("click", closeEditModal);
}

export async function loadCategories() {
  try {
    allCategories = await api.listCategories();
  } catch {
    allCategories = [];
  }

  // Populate all category dropdowns
  const selectors = [
    "category-select",
    "home-category-filter",
    "practice-category-filter",
    "edit-category-select",
  ];
  for (const id of selectors) {
    const el = document.getElementById(id);
    if (!el) continue;
    const current = el.value;
    const isFilter = id.includes("filter");
    const isEdit = id === "edit-category-select";
    el.innerHTML = isFilter
      ? '<option value="">All categories</option>'
      : isEdit
        ? '<option value="0">No category</option>'
        : '<option value="">No category</option>';
    for (const cat of allCategories) {
      el.innerHTML += `<option value="${cat.id}">${escapeHtml(cat.name)} (${cat.item_count})</option>`;
    }
    if (current) el.value = current;
  }
}

async function addItem() {
  const sourceText = document.getElementById("source-text").value.trim();
  if (!sourceText) return;

  const status = document.getElementById("add-status");
  setStatus(status, "Translating and generating audio...", "loading");

  const categorySelect = document.getElementById("category-select");
  const newCategoryInput = document.getElementById("new-category");

  const payload = { source_text: sourceText };
  if (newCategoryInput.value.trim()) {
    payload.category_name = newCategoryInput.value.trim();
  } else if (categorySelect.value) {
    payload.category_id = parseInt(categorySelect.value, 10);
  }

  try {
    await api.createItem(payload);
    document.getElementById("source-text").value = "";
    newCategoryInput.value = "";
    setStatus(status, "Item added!", "success");
    await loadCategories();
    await loadItems();
  } catch (e) {
    setStatus(status, e.message, "error");
  }
}

export async function loadItems() {
  const q = document.getElementById("home-search")?.value || "";
  const categoryId = document.getElementById("home-category-filter")?.value || "";

  const container = document.getElementById("items-list");
  try {
    const data = await api.listItems({ q, category_id: categoryId });
    container.innerHTML =
      data.items.length === 0
        ? '<p style="color:#868e96; text-align:center;">No items yet. Add one above!</p>'
        : data.items.map(renderHomeItem).join("");
    attachHomeListeners();
  } catch (e) {
    container.innerHTML = `<p class="status error">${escapeHtml(e.message)}</p>`;
  }
}

function renderHomeItem(item) {
  const catBadge = item.category
    ? `<span class="category-badge">${escapeHtml(item.category.name)}</span>`
    : "";
  const staleBadge = item.audio_stale ? '<span class="stale-badge">audio outdated</span>' : "";
  return `
    <div class="item-card" data-id="${item.id}">
        <div class="source">${escapeHtml(item.source_text)}</div>
        <div class="target">${escapeHtml(item.target_text)}</div>
        <div class="meta">${catBadge} ${staleBadge}</div>
        <div class="actions">
            ${item.audio_url ? `<button class="small btn-play" data-id="${item.id}">&#9654; Play</button>` : ""}
            ${item.audio_url ? `<a href="${api.audioDownloadUrl(item.id)}" class="small" style="padding:4px 10px;font-size:12px;text-decoration:none;border:1px solid #dee2e6;border-radius:6px;">&#11015; Download</a>` : ""}
            <button class="small btn-edit" data-id="${item.id}">Edit</button>
            ${item.audio_stale ? `<button class="small btn-regen" data-id="${item.id}">Regenerate Audio</button>` : ""}
            <button class="small danger btn-delete" data-id="${item.id}">Delete</button>
        </div>
        <audio id="audio-${item.id}" preload="none"></audio>
    </div>`;
}

function attachHomeListeners() {
  document.querySelectorAll("#items-list .btn-play").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      const audio = document.getElementById(`audio-${id}`);
      if (!audio.src) audio.src = api.audioUrl(id);
      audio.play();
    });
  });

  document.querySelectorAll("#items-list .btn-edit").forEach((btn) => {
    btn.addEventListener("click", () => openEditModal(parseInt(btn.dataset.id, 10)));
  });

  document.querySelectorAll("#items-list .btn-regen").forEach((btn) => {
    btn.addEventListener("click", async () => {
      btn.textContent = "Regenerating...";
      btn.disabled = true;
      try {
        await api.regenerateAudio(parseInt(btn.dataset.id, 10));
        await loadItems();
      } catch (e) {
        alert(e.message);
      }
    });
  });

  document.querySelectorAll("#items-list .btn-delete").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this item?")) return;
      try {
        await api.deleteItem(parseInt(btn.dataset.id, 10));
        await loadCategories();
        await loadItems();
      } catch (e) {
        alert(e.message);
      }
    });
  });
}

async function openEditModal(id) {
  const item = await api.getItem(id);
  document.getElementById("edit-item-id").value = item.id;
  document.getElementById("edit-target-text").value = item.target_text;
  document.getElementById("edit-category-select").value = item.category?.id || "0";
  document.getElementById("edit-modal").classList.remove("hidden");
  setStatus(document.getElementById("edit-status"), "");
}

function closeEditModal() {
  document.getElementById("edit-modal").classList.add("hidden");
}

async function saveEdit() {
  const id = parseInt(document.getElementById("edit-item-id").value, 10);
  const targetText = document.getElementById("edit-target-text").value.trim();
  const categoryId = parseInt(document.getElementById("edit-category-select").value, 10);
  const status = document.getElementById("edit-status");

  if (!targetText) {
    setStatus(status, "Target text cannot be empty", "error");
    return;
  }

  try {
    await api.updateItem(id, { target_text: targetText, category_id: categoryId });
    closeEditModal();
    await loadCategories();
    await loadItems();
  } catch (e) {
    setStatus(status, e.message, "error");
  }
}
