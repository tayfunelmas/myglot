export function setStatus(el, message, type = "") {
  el.textContent = message;
  el.className = `status ${type}`;
}

export function debounce(fn, ms = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

export function renderDiff(diff) {
  return diff
    .map((d) => {
      const cls = `diff-word ${d.status}`;
      return `<span class="${cls}">${escapeHtml(d.word)} </span>`;
    })
    .join("");
}

export function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

export function scoreClass(score) {
  if (score >= 80) return "score-high";
  if (score >= 50) return "score-mid";
  return "score-low";
}
