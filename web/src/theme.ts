import { icon } from "./icons";
import { $, store } from "./util";

type Theme = "light" | "dark";
const preferredTheme = (): Theme => {
  const saved = store("lumen.theme");
  return saved === "light" || saved === "dark" ? saved
    : window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

// Apply before fetching data so the page doesn't wait for the API to change theme.
export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
}
applyTheme(preferredTheme());

export function setupTheme(): void {
  const button = $("themeToggle");
  const updateButton = () => {
    const dark = document.documentElement.dataset.theme === "dark";
    button.innerHTML = icon(dark ? "sun" : "moon");
    button.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    button.setAttribute("aria-pressed", String(dark));
    button.title = dark ? "Switch to light mode" : "Switch to dark mode";
  };
  updateButton();
  button.addEventListener("click", () => {
    const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(theme);
    store("lumen.theme", theme);
    updateButton();
  });
}
