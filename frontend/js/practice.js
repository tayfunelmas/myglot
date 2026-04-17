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
  const categoryId = document.getElementById("practice-category-filter")?.value || "";
  const container = document.getElementById("practice-list");

  try {
    const data = await api.listItems({ category_id: categoryId });
    container.innerHTML =
      data.items.length === 0
        ? '<p style="color:#868e96; text-align:center;">No items to practice. Add some from the Home tab!</p>'
        : data.items.map(renderPracticeItem).join("");
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
    <div class="item-card" data-id="${item.id}">
        <div class="source">${escapeHtml(item.source_text)}</div>
        <div class="target hidden-text" id="target-${item.id}" data-revealed="false">${escapeHtml(item.target_text)}</div>
        <div class="meta">${catBadge}</div>
        <div class="actions">
            <button class="small btn-reveal" data-id="${item.id}">Reveal</button>
            ${item.audio_url ? `<button class="small btn-play" data-id="${item.id}">&#9654; Play</button>` : ""}
            ${item.audio_url ? `<a href="${api.audioDownloadUrl(item.id)}" class="small" style="padding:4px 10px;font-size:12px;text-decoration:none;border:1px solid #dee2e6;border-radius:6px;">&#11015; Download</a>` : ""}
            <button class="small btn-record" data-id="${item.id}">&#127908; Record</button>
        </div>
        <audio id="practice-audio-${item.id}" preload="none"></audio>
        <div id="result-${item.id}"></div>
    </div>`;
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
