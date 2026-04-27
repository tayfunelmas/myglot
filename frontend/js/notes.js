import { api } from "./api.js";
import { escapeHtml, setStatus } from "./util.js";

export async function initNotes() {
  await loadNotes();

  document.getElementById("btn-add-note").addEventListener("click", addNote);

  // Edit modal
  document.getElementById("btn-note-edit-cancel").addEventListener("click", closeEditModal);
  document.getElementById("btn-note-edit-save").addEventListener("click", saveEditNote);

  // Close modal on overlay click
  document.getElementById("note-edit-modal").addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) closeEditModal();
  });
}

export async function loadNotes() {
  const list = document.getElementById("notes-list");
  try {
    const notes = await api.listNotes();
    if (notes.length === 0) {
      list.innerHTML = '<p class="empty-message">No notes yet. Add your first note above.</p>';
      return;
    }
    list.innerHTML = notes.map(renderNoteCard).join("");
    list.querySelectorAll(".btn-edit-note").forEach((btn) => {
      btn.addEventListener("click", () => openEditModal(btn.dataset.id));
    });
    list.querySelectorAll(".btn-delete-note").forEach((btn) => {
      btn.addEventListener("click", () => deleteNote(btn.dataset.id));
    });
  } catch (e) {
    list.innerHTML = `<p class="status error">${escapeHtml(e.message)}</p>`;
  }
}

function renderNoteCard(note) {
  const renderedBody =
    typeof marked !== "undefined" ? marked.parse(note.body || "") : escapeHtml(note.body || "");
  const date = new Date(note.created_at).toLocaleDateString();
  return `<div class="note-card card">
      <div class="note-card-header">
        <h3 class="note-card-title">${escapeHtml(note.title)}</h3>
        <div class="note-card-actions">
          <button type="button" class="icon-btn btn-edit-note" data-id="${note.id}" title="Edit">
            <span class="material-symbols-rounded">edit</span>
          </button>
          <button type="button" class="icon-btn btn-delete-note" data-id="${note.id}" title="Delete">
            <span class="material-symbols-rounded">delete</span>
          </button>
        </div>
      </div>
      <div class="note-card-body markdown-body">${renderedBody}</div>
      <div class="note-card-date">${date}</div>
    </div>`;
}

async function addNote() {
  const titleEl = document.getElementById("note-title");
  const bodyEl = document.getElementById("note-body");
  const statusEl = document.getElementById("note-add-status");
  const title = titleEl.value.trim();
  if (!title) {
    setStatus(statusEl, "Title is required", "error");
    return;
  }
  try {
    await api.createNote({ title, body: bodyEl.value });
    titleEl.value = "";
    bodyEl.value = "";
    setStatus(statusEl, "Note added", "success");
    await loadNotes();
  } catch (e) {
    setStatus(statusEl, e.message, "error");
  }
}

async function openEditModal(id) {
  const note = await api.getNote(id);
  document.getElementById("note-edit-id").value = note.id;
  document.getElementById("note-edit-title").value = note.title;
  document.getElementById("note-edit-body").value = note.body;
  document.getElementById("note-edit-status").textContent = "";
  document.getElementById("note-edit-modal").classList.remove("hidden");
}

function closeEditModal() {
  document.getElementById("note-edit-modal").classList.add("hidden");
}

async function saveEditNote() {
  const id = document.getElementById("note-edit-id").value;
  const title = document.getElementById("note-edit-title").value.trim();
  const body = document.getElementById("note-edit-body").value;
  const statusEl = document.getElementById("note-edit-status");
  if (!title) {
    setStatus(statusEl, "Title is required", "error");
    return;
  }
  try {
    await api.updateNote(id, { title, body });
    closeEditModal();
    await loadNotes();
  } catch (e) {
    setStatus(statusEl, e.message, "error");
  }
}

async function deleteNote(id) {
  if (!confirm("Delete this note?")) return;
  try {
    await api.deleteNote(id);
    await loadNotes();
  } catch (e) {
    alert(e.message);
  }
}
