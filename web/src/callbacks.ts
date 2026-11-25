import { select } from "./actions";
import { brandChip } from "./format";
import { icon } from "./icons";
import { state } from "./state";
import { compactChips } from "./traits";
import type { CallbackRow, CallbackSection } from "./types";
import { $, api, esc } from "./util";

const SECTIONS: Array<[CallbackSection, string]> = [
  ["expecting", "Expecting call"], ["overdue", "Overdue"], ["today", "Today"], ["upcoming", "Upcoming · next 7 days"]];
const URGENT: CallbackSection[] = ["expecting", "overdue", "today"];

const digits = (s: string | null): string => (s ?? "").replace(/\D/g, "");

/** "Today 14:00", "Tue Nov 25", "Mon Nov 24 09:30". */
export function when(at: string | null, today = new Date()): string {
  if (!at) return "";
  const [y, m, d] = at.slice(0, 10).split("-").map(Number) as [number, number, number];
  const date = new Date(y, m - 1, d), time = at.slice(11, 16);
  const same = date.toDateString() === today.toDateString();
  const day = same ? "Today" : date.toLocaleDateString("en-CA", { weekday: "short", month: "short", day: "numeric" });
  return time ? `${day} ${time}` : day;
}

export function matchesCallback(r: CallbackRow, query: string): boolean {
  const q = query.trim().toLowerCase(), n = digits(q);
  if (!q) return true;
  return r.name.toLowerCase().includes(q) || (r.contact?.name.toLowerCase().includes(q) ?? false)
    || (n.length >= 3 && digits(r.phone).includes(n));
}

function rowHtml(r: CallbackRow): string {
  const who = r.contact ? `${esc(r.contact.name)}${r.contact.title ? ` <span class="hint">(${esc(r.contact.title)})</span>` : ""}` : '<span class="hint">No contact on file</span>';
  const phone = r.phone ? `${esc(r.phone)}${r.ext ? ` ext ${esc(r.ext)}` : ""}` : "No phone on file";
  return `<button type="button" class="callback-row${r.late ? " callback-late" : ""}" data-callback="${r.id}">
    <span class="callback-top"><strong>${esc(r.name)}</strong>${brandChip(r.brand)}<span class="callback-when">${esc(when(r.callback_at))}${r.late ? " · late" : ""}</span></span>
    <span class="callback-who">${who} · ${phone}</span>
    ${r.last_note ? `<span class="callback-note">${esc(r.last_note)}</span>` : ""}
    <span class="callback-chips">${compactChips(r.traits, r.badges)}</span>
  </button>`;
}

export function renderCallbacks(): void {
  const count = state.callbacks.filter(r => URGENT.includes(r.section)).length;
  const badge = $("callbacksBadge");
  badge.hidden = count === 0; badge.textContent = String(count);
  $("callbacksBtn").setAttribute("aria-label", `Callbacks: ${count} need attention`);
  const q = $<HTMLInputElement>("callbacksSearch").value;
  const rows = state.callbacks.filter(r => matchesCallback(r, q));
  $("callbacksList").innerHTML = SECTIONS.map(([s, label]) => {
    const items = rows.filter(r => r.section === s);
    return items.length ? `<section class="callback-section callback-${s}"><h4>${label} <b>${items.length}</b></h4>${items.map(rowHtml).join("")}</section>` : "";
  }).join("") || `<p class="hint callback-empty">${q ? "No callbacks match." : "No callbacks scheduled."}</p>`;
}

export async function loadCallbacks(): Promise<void> {
  state.callbacks = await api<CallbackRow[]>("/api/callbacks");
  renderCallbacks();
}

export function bindCallbacks(): void {
  const btn = $("callbacksBtn"), panel = $("callbacksPanel");
  btn.insertAdjacentHTML("afterbegin", icon("bell"));
  const open = (on: boolean) => {
    panel.hidden = !on; btn.setAttribute("aria-expanded", String(on));
    if (on) { void loadCallbacks(); $("callbacksSearch").focus(); }
  };
  btn.addEventListener("click", () => open(panel.hidden === true));
  document.addEventListener("click", e => {
    const el = e.target as Element;
    if (!panel.hidden && !panel.contains(el) && !btn.contains(el)) open(false);
  });
  panel.addEventListener("keydown", e => {
    e.stopPropagation();
    if (e.key === "Escape") { open(false); btn.focus(); }
    if (e.key === "Enter" && (e.target as HTMLElement).id === "callbacksSearch") {
      const first = panel.querySelector<HTMLElement>("[data-callback]");
      if (first) { e.preventDefault(); first.click(); }
    }
  });
  $("callbacksSearch").addEventListener("input", renderCallbacks);
  $("callbacksList").addEventListener("click", e => {
    const row = (e.target as Element).closest<HTMLElement>("[data-callback]");
    if (row) { open(false); void select(Number(row.dataset.callback)); }
  });
}
