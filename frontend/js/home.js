import { api } from "./api.js";
import { debounce, escapeHtml, setStatus } from "./util.js";

let allCategories = [];

export async function initHome() {
  await loadCategories();
  await loadItems();

  document.getElementById("btn-translate").addEventListener("click", translateSource);
  document.getElementById("btn-translate-back").addEventListener("click", translateBack);
  document.getElementById("btn-gen-audio").addEventListener("click", previewAudio);
  document.getElementById("btn-add-item").addEventListener("click", addItem);
  document.getElementById("home-search").addEventListener(
    "input",
    debounce(() => loadItems()),
  );
  document.getElementById("home-category-filter").addEventListener("change", () => loadItems());

  // Edit modal
  document.getElementById("btn-edit-save").addEventListener("click", saveEdit);
  document.getElementById("btn-edit-regen").addEventListener("click", regenerateFromEditModal);
  document.getElementById("btn-edit-cancel").addEventListener("click", closeEditModal);
}

export async function loadCategories() {
  try {
    allCategories = await api.listCategories();
  } catch {
    allCategories = [];
  }

  // Populate filter multi-selects
  const filterIds = ["home-category-filter", "practice-category-filter"];
  for (const id of filterIds) {
    const el = document.getElementById(id);
    if (!el) continue;
    const saved = JSON.parse(localStorage.getItem(`myglot_${id}`) || "[]");
    el.innerHTML = "";
    for (const cat of allCategories) {
      const opt = document.createElement("option");
      opt.value = String(cat.id);
      opt.textContent = `${cat.name} (${cat.item_count})`;
      if (saved.includes(String(cat.id))) opt.selected = true;
      el.appendChild(opt);
    }
  }

  // Populate single-select dropdowns (add-item, edit modal)
  const singleIds = ["category-select", "edit-category-select"];
  for (const id of singleIds) {
    const el = document.getElementById(id);
    if (!el) continue;
    const current = el.value;
    const isEdit = id === "edit-category-select";
    el.innerHTML = isEdit
      ? '<option value="0">No category</option>'
      : '<option value="">No category</option>';
    for (const cat of allCategories) {
      el.innerHTML += `<option value="${cat.id}">${escapeHtml(cat.name)} (${cat.item_count})</option>`;
    }
    if (current) el.value = current;
  }
}

async function translateSource() {
  const sourceText = document.getElementById("source-text").value.trim();
  if (!sourceText) return;

  const status = document.getElementById("add-status");
  setStatus(status, "Translating...", "loading");

  try {
    const result = await api.translate(sourceText);
    document.getElementById("target-text").value = result.target_text;
    setStatus(status, "Translation ready — edit if needed.", "success");
  } catch (e) {
    setStatus(status, e.message, "error");
  }
}

async function translateBack() {
  const targetText = document.getElementById("target-text").value.trim();
  if (!targetText) return;

  const status = document.getElementById("add-status");
  setStatus(status, "Translating back...", "loading");

  try {
    const result = await api.translateBack(targetText);
    document.getElementById("source-text").value = result.source_text;
    setStatus(status, "Reverse translation ready — edit if needed.", "success");
  } catch (e) {
    setStatus(status, e.message, "error");
  }
}

async function previewAudio() {
  const targetText = document.getElementById("target-text").value.trim();
  if (!targetText) {
    const status = document.getElementById("add-status");
    setStatus(status, "Enter or generate a translation first.", "error");
    return;
  }

  const status = document.getElementById("add-status");
  setStatus(status, "Generating audio preview...", "loading");

  try {
    const blob = await api.ttsPreview(targetText);
    const url = URL.createObjectURL(blob);
    const preview = document.getElementById("audio-preview");
    preview.innerHTML = "";
    const audio = document.createElement("audio");
    audio.controls = true;
    audio.src = url;
    preview.appendChild(audio);
    audio.play();
    setStatus(status, "Audio preview ready.", "success");
  } catch (e) {
    setStatus(status, e.message, "error");
  }
}

async function addItem() {
  const sourceText = document.getElementById("source-text").value.trim();
  const targetText = document.getElementById("target-text").value.trim();
  if (!sourceText) return;

  const status = document.getElementById("add-status");
  setStatus(status, "Adding item...", "loading");

  const categorySelect = document.getElementById("category-select");
  const newCategoryInput = document.getElementById("new-category");

  const payload = { source_text: sourceText };
  if (targetText) payload.target_text = targetText;
  if (newCategoryInput.value.trim()) {
    payload.category_name = newCategoryInput.value.trim();
  } else if (categorySelect.value) {
    payload.category_id = parseInt(categorySelect.value, 10);
  }

  try {
    await api.createItem(payload);
    document.getElementById("source-text").value = "";
    document.getElementById("target-text").value = "";
    document.getElementById("audio-preview").innerHTML = "";
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
  const filterEl = document.getElementById("home-category-filter");
  const selectedIds = filterEl ? [...filterEl.selectedOptions].map((o) => o.value) : [];
  // Persist selection
  localStorage.setItem("myglot_home-category-filter", JSON.stringify(selectedIds));

  const container = document.getElementById("items-list");
  try {
    const params = { q };
    if (selectedIds.length > 0) params.category_ids = selectedIds.join(",");
    const data = await api.listItems(params);
    if (data.items.length === 0) {
      container.innerHTML =
        '<p style="color:var(--md-sys-color-on-surface-variant); text-align:center;">No items yet. Add one above!</p>';
    } else {
      container.innerHTML = `
        <table class="items-table">
          <thead>
            <tr>
              <th class="col-drag"></th>
              <th class="col-source">Source</th>
              <th class="col-target">Translation</th>
              <th class="col-meta">Category</th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody id="items-tbody">
            ${data.items.map(renderHomeItem).join("")}
          </tbody>
        </table>`;
      initDragAndDrop();
    }
    attachHomeListeners();
  } catch (e) {
    container.innerHTML = `<p class="status error">${escapeHtml(e.message)}</p>`;
  }
}

function renderHomeItem(item) {
  const catBadge = item.category
    ? `<span class="category-badge">${escapeHtml(item.category.name)}</span>`
    : "";
  const staleBadge = item.audio_stale ? '<span class="stale-badge">stale</span>' : "";
  return `
    <tr class="item-row" draggable="true" data-id="${item.id}">
      <td class="col-drag"><span class="drag-handle material-symbols-rounded" title="Drag to reorder">drag_indicator</span></td>
      <td class="col-source">${escapeHtml(item.source_text)}</td>
      <td class="col-target">${escapeHtml(item.target_text)} ${staleBadge}</td>
      <td class="col-meta">${catBadge}</td>
      <td class="col-actions">
        <div class="row-actions">
          ${item.audio_url ? `<button type="button" class="icon-btn btn-play" data-id="${item.id}" title="Play audio"><span class="material-symbols-rounded">play_arrow</span></button>` : ""}
          <button type="button" class="icon-btn btn-edit" data-id="${item.id}" title="Edit"><span class="material-symbols-rounded">edit</span></button>
          <button type="button" class="icon-btn danger btn-delete" data-id="${item.id}" title="Delete"><span class="material-symbols-rounded">delete</span></button>
        </div>
        <audio id="audio-${item.id}" preload="none"></audio>
      </td>
    </tr>`;
}

let _dragSrcRow = null;

function initDragAndDrop() {
  const tbody = document.getElementById("items-tbody");
  if (!tbody) return;

  tbody.addEventListener("dragstart", (e) => {
    const row = e.target.closest("tr.item-row");
    if (!row) return;
    _dragSrcRow = row;
    row.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", row.dataset.id);
  });

  tbody.addEventListener("dragend", (e) => {
    const row = e.target.closest("tr.item-row");
    if (row) {
      row.classList.remove("dragging");
    }
    _dragSrcRow = null;
    tbody.querySelectorAll("tr.item-row").forEach((r) => {
      r.classList.remove("drag-over");
    });
  });

  tbody.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    const targetRow = e.target.closest("tr.item-row");
    if (!targetRow || targetRow === _dragSrcRow) return;
    tbody.querySelectorAll("tr.item-row").forEach((r) => {
      r.classList.remove("drag-over");
    });
    targetRow.classList.add("drag-over");
  });

  tbody.addEventListener("drop", async (e) => {
    e.preventDefault();
    const targetRow = e.target.closest("tr.item-row");
    if (!targetRow || !_dragSrcRow || targetRow === _dragSrcRow) return;

    // Move DOM row
    const rows = [...tbody.querySelectorAll("tr.item-row")];
    const srcIdx = rows.indexOf(_dragSrcRow);
    const tgtIdx = rows.indexOf(targetRow);
    if (srcIdx < tgtIdx) {
      targetRow.after(_dragSrcRow);
    } else {
      targetRow.before(_dragSrcRow);
    }

    // Persist new order
    const newOrder = [...tbody.querySelectorAll("tr.item-row")].map((r) =>
      parseInt(r.dataset.id, 10),
    );
    try {
      await api.reorderItems(newOrder);
    } catch (err) {
      console.error("Reorder failed:", err);
      await loadItems(); // reload on failure
    }
  });
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

async function regenerateFromEditModal() {
  const id = parseInt(document.getElementById("edit-item-id").value, 10);
  const targetText = document.getElementById("edit-target-text").value.trim();
  const categoryId = parseInt(document.getElementById("edit-category-select").value, 10);
  const status = document.getElementById("edit-status");
  const btnRegen = document.getElementById("btn-edit-regen");
  const btnSave = document.getElementById("btn-edit-save");

  if (!targetText) {
    setStatus(status, "Target text cannot be empty", "error");
    return;
  }

  const prevLabel = btnRegen.textContent;
  btnRegen.textContent = "Regenerating...";
  btnRegen.disabled = true;
  btnSave.disabled = true;
  setStatus(status, "Regenerating audio...", "loading");

  try {
    // Ensure any edits are saved before regenerating audio.
    await api.updateItem(id, { target_text: targetText, category_id: categoryId });
    await api.regenerateAudio(id);
    setStatus(status, "Audio regenerated.", "success");
    await loadCategories();
    await loadItems();
  } catch (e) {
    setStatus(status, e.message, "error");
  } finally {
    btnRegen.textContent = prevLabel;
    btnRegen.disabled = false;
    btnSave.disabled = false;
  }
}
