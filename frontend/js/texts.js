import { api } from "./api.js";
import { escapeHtml, setStatus } from "./util.js";

export async function initTexts() {
  await loadTexts();
  document.getElementById("btn-generate-text").addEventListener("click", generateText);
}

export async function loadTexts() {
  const list = document.getElementById("texts-list");
  try {
    const texts = await api.listTexts();
    if (texts.length === 0) {
      list.innerHTML =
        '<p class="empty-message">No generated texts yet. Describe what you want to learn above.</p>';
      return;
    }
    list.innerHTML = texts.map(renderTextCard).join("");
    list.querySelectorAll(".btn-play-text").forEach((btn) => {
      btn.addEventListener("click", () => playTextAudio(btn.dataset.id));
    });
    list.querySelectorAll(".btn-delete-text").forEach((btn) => {
      btn.addEventListener("click", () => deleteText(btn.dataset.id));
    });
    list.querySelectorAll(".btn-regen-text-audio").forEach((btn) => {
      btn.addEventListener("click", () => regenAudio(btn.dataset.id));
    });
    list.querySelectorAll(".btn-toggle-vocab").forEach((btn) => {
      btn.addEventListener("click", () => toggleVocab(btn));
    });
  } catch (e) {
    list.innerHTML = `<p class="status error">${escapeHtml(e.message)}</p>`;
  }
}

function renderTextCard(text) {
  const renderedVocab =
    typeof marked !== "undefined"
      ? marked.parse(text.vocabulary_md || "")
      : escapeHtml(text.vocabulary_md || "");
  const date = new Date(text.created_at).toLocaleDateString();
  const hasAudio = !!text.audio_url;
  return `<div class="text-card card">
      <div class="text-card-header">
        <h3 class="text-card-title">${escapeHtml(text.title)}</h3>
        <div class="text-card-actions">
          ${
            hasAudio
              ? `<button type="button" class="icon-btn btn-play-text" data-id="${text.id}" title="Play audio">
            <span class="material-symbols-rounded">play_arrow</span>
          </button>`
              : ""
          }
          <button type="button" class="icon-btn btn-regen-text-audio" data-id="${text.id}" title="Regenerate audio">
            <span class="material-symbols-rounded">refresh</span>
          </button>
          <button type="button" class="icon-btn btn-delete-text" data-id="${text.id}" title="Delete">
            <span class="material-symbols-rounded">delete</span>
          </button>
        </div>
      </div>
      <div class="text-card-body">${escapeHtml(text.body)}</div>
      <div class="text-card-vocab-toggle">
        <button type="button" class="btn btn-text btn-toggle-vocab" data-expanded="false">
          <span class="material-symbols-rounded">dictionary</span>
          Show Vocabulary
        </button>
      </div>
      <div class="text-card-vocab hidden markdown-body">${renderedVocab}</div>
      <div class="text-card-date">${date}</div>
    </div>`;
}

function toggleVocab(btn) {
  const card = btn.closest(".text-card");
  const vocabDiv = card.querySelector(".text-card-vocab");
  const expanded = btn.dataset.expanded === "true";
  if (expanded) {
    vocabDiv.classList.add("hidden");
    btn.dataset.expanded = "false";
    btn.innerHTML = '<span class="material-symbols-rounded">dictionary</span> Show Vocabulary';
  } else {
    vocabDiv.classList.remove("hidden");
    btn.dataset.expanded = "true";
    btn.innerHTML = '<span class="material-symbols-rounded">dictionary</span> Hide Vocabulary';
  }
}

async function generateText() {
  const input = document.getElementById("text-instructions");
  const statusEl = document.getElementById("text-gen-status");
  const btn = document.getElementById("btn-generate-text");
  const instructions = input.value.trim();
  if (!instructions) {
    setStatus(statusEl, "Please enter instructions", "error");
    return;
  }
  btn.disabled = true;
  setStatus(statusEl, "Generating text, audio & vocabulary... This may take a moment.", "info");
  try {
    await api.createText(instructions);
    input.value = "";
    setStatus(statusEl, "Text generated successfully", "success");
    await loadTexts();
  } catch (e) {
    setStatus(statusEl, e.message, "error");
  } finally {
    btn.disabled = false;
  }
}

let _currentAudio = null;

function playTextAudio(id) {
  if (_currentAudio) {
    _currentAudio.pause();
    _currentAudio = null;
  }
  _currentAudio = new Audio(api.textAudioUrl(id));
  _currentAudio.play();
}

async function deleteText(id) {
  if (!confirm("Delete this generated text?")) return;
  try {
    await api.deleteText(id);
    await loadTexts();
  } catch (e) {
    alert(e.message);
  }
}

async function regenAudio(id) {
  const btn = document.querySelector(`.btn-regen-text-audio[data-id="${id}"]`);
  if (btn) btn.disabled = true;
  try {
    await api.regenerateTextAudio(id);
    await loadTexts();
  } catch (e) {
    alert(e.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}
