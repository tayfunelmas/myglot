import { api } from "./api.js";
import { Recorder } from "./recorder.js";
import { escapeHtml, renderDiff, scoreClass } from "./util.js";

const recorder = new Recorder();

export async function initPractice() {
  document
    .getElementById("practice-category-filter")
    .addEventListener("change", () => loadPracticeItems());
}

export async function loadPracticeItems() {
  const filterEl = document.getElementById("practice-category-filter");
  const selectedIds = filterEl ? [...filterEl.selectedOptions].map((o) => o.value) : [];
  // Persist selection
  localStorage.setItem("myglot_practice-category-filter", JSON.stringify(selectedIds));
  const container = document.getElementById("practice-list");

  try {
    const params = {};
    if (selectedIds.length > 0) params.category_ids = selectedIds.join(",");
    const data = await api.listItems(params);
    if (data.items.length === 0) {
      container.innerHTML =
        '<p style="color:#868e96; text-align:center;">No items to practice. Add some from the Home tab!</p>';
    } else {
      container.innerHTML = `
        <table class="items-table practice-table">
          <thead>
            <tr>
              <th class="col-source">Source</th>
              <th class="col-target">Translation</th>
              <th class="col-meta">Category</th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${data.items.map(renderPracticeItem).join("")}
          </tbody>
        </table>`;
    }
    attachPracticeListeners();
  } catch (e) {
    container.innerHTML = `<p class="status error">${escapeHtml(e.message)}</p>`;
  }
}

function renderPracticeItem(item) {
  const catBadge = item.category
    ? `<span class="category-badge">${escapeHtml(item.category.name)}</span>`
    : "";
  return `
    <tr class="item-row" data-id="${item.id}">
      <td class="col-source">${escapeHtml(item.source_text)}</td>
      <td class="col-target">
        <span class="target-text hidden-text" id="target-${item.id}" data-revealed="false">${escapeHtml(item.target_text)}</span>
      </td>
      <td class="col-meta">${catBadge}</td>
      <td class="col-actions">
        <div class="row-actions">
          <button type="button" class="icon-btn btn-reveal" data-id="${item.id}" title="Reveal / Hide">&#128065;</button>
          ${item.audio_url ? `<button type="button" class="icon-btn btn-play" data-id="${item.id}" title="Play audio">&#9654;</button>` : ""}
          ${item.audio_url ? `<a href="${api.audioDownloadUrl(item.id)}" class="icon-btn" title="Download audio" style="text-decoration:none;">&#11015;</a>` : ""}
          <button type="button" class="icon-btn btn-record" data-id="${item.id}" title="Record">&#127908;</button>
        </div>
        <audio id="practice-audio-${item.id}" preload="none"></audio>
        <div id="result-${item.id}"></div>
      </td>
    </tr>`;
}

function attachPracticeListeners() {
  // Reveal buttons
  document.querySelectorAll("#practice-list .btn-reveal").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      const el = document.getElementById(`target-${id}`);
      const revealed = el.dataset.revealed === "true";
      if (revealed) {
        el.classList.add("hidden-text");
        el.dataset.revealed = "false";
        btn.textContent = "Reveal";
      } else {
        el.classList.remove("hidden-text");
        el.dataset.revealed = "true";
        btn.textContent = "Hide";
      }
    });
  });

  // Play buttons
  document.querySelectorAll("#practice-list .btn-play").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      const audio = document.getElementById(`practice-audio-${id}`);
      if (!audio.src) audio.src = api.audioUrl(id);
      audio.play();
    });
  });

  // Record buttons
  document.querySelectorAll("#practice-list .btn-record").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;

      if (recorder.recording) {
        // Stop recording
        btn.textContent = "&#127908; Record";
        btn.classList.remove("recording");
        const blob = await recorder.stop();

        const resultDiv = document.getElementById(`result-${id}`);
        resultDiv.innerHTML = '<p class="status loading">Processing...</p>';

        try {
          const result = await api.practice(id, blob);
          resultDiv.innerHTML = `
                        <div class="practice-result">
                            <div class="score ${scoreClass(result.score)}">${result.score}/100</div>
                            <div class="transcript">You said: "${escapeHtml(result.transcript)}"</div>
                            <div class="diff">${renderDiff(result.diff)}</div>
                        </div>`;
        } catch (e) {
          resultDiv.innerHTML = `<p class="status error">${escapeHtml(e.message)}</p>`;
        }
      } else {
        // Start recording
        try {
          await recorder.start();
          btn.textContent = "⏹ Stop";
          btn.classList.add("recording");
        } catch (e) {
          alert(`Could not access microphone: ${e.message}`);
        }
      }
    });
  });
}
