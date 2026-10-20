import { icon } from "./icons";
import { $, store } from "./util";
export function setupShell(): void {
  const sidebar = $("sidebar"), toggle = $("collapseSidebar");
  const apply = (collapsed: boolean) => {
    sidebar.classList.toggle("collapsed", collapsed);
    toggle.setAttribute("aria-expanded", String(!collapsed));
    toggle.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
    store("lumen.sidebar", String(collapsed));
  };
  toggle.innerHTML = icon("panel");
  apply(store("lumen.sidebar") === "true");
  toggle.addEventListener("click", () => apply(!sidebar.classList.contains("collapsed")));
  $("filterIcon").innerHTML = icon("filter");
  for (const id of ["copyName", "copyAppt"]) {
    const el = $(id); el.innerHTML = icon("copy") + (id === "copyAppt" ? " Copy appointment" : "");
    el.setAttribute("aria-label", id === "copyAppt" ? "Copy appointment" : "Copy company name");
  }
  document.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>("input, select, textarea").forEach(el => {
    if (!el.getAttribute("aria-label") && !el.closest("label")) el.setAttribute("aria-label", el.getAttribute("placeholder") || el.getAttribute("title") || el.name || el.id);
  });
  const searchIcon = $("search").previousElementSibling;
  if (searchIcon) searchIcon.innerHTML = icon("search");
}
