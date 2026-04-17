import { initHome, loadCategories, loadItems } from "./home.js";
import { initPractice, loadPracticeItems } from "./practice.js";
import { initSettings } from "./settings.js";

// Tab switching
const tabs = document.querySelectorAll(".tab");
const contents = document.querySelectorAll(".tab-content");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;

    tabs.forEach((t) => {
      t.classList.remove("active");
    });
    contents.forEach((c) => {
      c.classList.remove("active");
    });

    tab.classList.add("active");
    document.getElementById(target).classList.add("active");

    // Refresh data when switching tabs
    if (target === "home") {
      loadCategories();
      loadItems();
    } else if (target === "practice") {
      loadCategories();
      loadPracticeItems();
    }
  });
});

// Initialize all modules
(async () => {
  await initHome();
  await initPractice();
  await initSettings();
})();
