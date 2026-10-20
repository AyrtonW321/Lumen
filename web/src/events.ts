import { bindContacts } from "./contact-events";
import { closeLead, patch, pickOutcome, refresh, reloadDetail, resetForm, save, select } from "./actions";
import { QUICK, type QuickKind } from "./constants";
import { quickDate } from "./dates";
import { renderList, renderPanel, renderPreview, showModel } from "./render";
import { config, currentLead, state } from "./state";
import type { ModelMetrics, Source, SyncCounts, TabId } from "./types";
import { $, api, copy, errorMessage, store, toast } from "./util";

/** The closest ancestor of an event target matching `selector`. */
const closest = (e: Event, selector: string): HTMLElement | null => (e.target as Element).closest<HTMLElement>(selector);

function onKeydown(e: KeyboardEvent): void {
  const el = document.activeElement as HTMLElement, typing = ["INPUT", "SELECT", "TEXTAREA"].includes(el.tagName);
  const { detail, view, sel, form } = state;
  if (e.key === "Escape") { el.blur(); resetForm(); return; }
  if (e.key === "Enter" && detail && !el.closest("form") && el.id !== "search" && el.tagName !== "BUTTON"
      && (!typing || el.tagName !== "TEXTAREA" || e.ctrlKey)) { e.preventDefault(); void save(); return; }
  if (typing) return;
  if (e.key === "/") { e.preventDefault(); $("search").focus(); return; }
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    const i = view.findIndex(l => l.id === sel), j = Math.max(0, Math.min(view.length - 1, i + (e.key === "ArrowDown" ? 1 : -1)));
    const next = view[j];
    if (next) void select(next.id);
    return;
  }
  if (!detail || e.ctrlKey || e.metaKey || e.altKey) return;
  const outcomes = config().outcomes;
  const code = Object.keys(outcomes).find(c => outcomes[c]?.key === e.key.toLowerCase());
  const contact = /^[1-9]$/.test(e.key) ? detail.contacts[+e.key - 1] : undefined;
  if (code) pickOutcome(code);
  else if (e.key === "0") form.contact_id = null;
  else if (contact) form.contact_id = contact.id;
  else return;
  renderPanel();
}

function bindLeadList(): void {
  for (const id of ["search", "fBrand", "fProduct", "fDue", "fStatus", "fQuality"]) $(id).addEventListener("input", renderList);
  $("resetFilters").addEventListener("click", () => {
    for (const id of ["fBrand", "fStatus", "fQuality"]) $<HTMLSelectElement>(id).value = "";
    $("fProduct").querySelectorAll<HTMLInputElement>("input").forEach(i => i.checked = false);
    $<HTMLInputElement>("fDue").checked = false; renderList();
  });
  $("tabs").addEventListener("click", e => {
    const b = closest(e, "[data-tab]");
    if (b) { state.tab = b.dataset.tab as TabId; store("lumen.tab", state.tab); renderList(); }
  });
  $("search").addEventListener("keydown", e => {
    const first = state.view[0];
    if (e.key === "Enter" && first) { e.preventDefault(); e.stopPropagation(); void select(first.id); $("search").blur(); }
  });
  $("list").addEventListener("click", e => { const el = closest(e, "[data-id]"); if (el) void select(Number(el.dataset.id)); });
  const form = $<HTMLFormElement>("newLead");
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const { product: _product, ...fields } = Object.fromEntries(new FormData(form));
    const products = [...form.querySelectorAll<HTMLInputElement>("input[name=product]:checked")].map(i => i.value);
    try {
      const { id } = await api<{ id: number }>("/api/leads", { ...fields, products });
      form.reset(); state.tab = fields.source as Source; await refresh(); void select(id);
    } catch (err) { toast(errorMessage(err)); }
  });
}

function bindLeadHeader(): void {
  $("panel").addEventListener("click", e => {
    const c = closest(e, "[data-copy]");
    if (c) { e.stopPropagation(); void copy(c.dataset.copy ?? "", c.dataset.label ?? ""); }
  });
  $("lProducts").addEventListener("click", e => {
    const p = closest(e, "[data-p]")?.dataset.p; if (!p) return;
    const set = new Set(currentLead().products.split(",").filter(Boolean));
    if (!set.delete(p)) set.add(p);
    void patch({ products: [...set] });
  });
  $("lBrand").addEventListener("change", e => void patch({ brand: (e.target as HTMLSelectElement).value }));
  $("lSource").addEventListener("change", e => {
    const source = (e.target as HTMLSelectElement).value as Source;
    void patch({ source }, `Moved to ${config().sources[source]}`);
  });
  $("winner").addEventListener("click", () => void patch({ source: "winner" }, "Marked as winner"));
  $("loser").addEventListener("click", () => void patch({ source: "loser" }, "Marked as loser"));
  $("close").addEventListener("click", closeLead);
  $("copyName").addEventListener("click", () => void copy(currentLead().name, "company name"));
  for (const label of ["good", "poor"] as const) {
    $(label).addEventListener("click", () => void patch({ label: currentLead().label === label ? null : label }));
  }
}

function bindActivityLog(): void {
  $("outcomes").addEventListener("change", e => { const value = (e.target as HTMLSelectElement).value; state.form.outcome = value || null; if (value) pickOutcome(value); renderPanel(); });
  $("quick").innerHTML = '<option value="">Quick callback date</option>' + QUICK.map(([k,l]) => `<option value="${k}">${l}</option>`).join("");
  $("quick").addEventListener("change", e => { const el = e.target as HTMLSelectElement; if (el.value) { $<HTMLInputElement>("callback_date").value = quickDate(el.value as QuickKind); el.value = ""; renderPreview(); } });
  $("reschedule").addEventListener("click", () => {
    const d = $<HTMLInputElement>("callback_date").value;
    if (!d) return toast("Pick a date or a quick button first");
    void patch({ next_action_date: d }, `Next call set to ${d}`);
  });
  for (const id of ["callback_date", "note"]) $(id).addEventListener("input", renderPreview);
  $("save").addEventListener("click", () => void save());
}

function bindDetails(): void {
  const form = $<HTMLFormElement>("detailsForm");
  $("saveDetails").addEventListener("click", () => { void saveAppointmentFields(form).catch(() => {}); });
  $("copyAppt").addEventListener("click", async () => {
    try {
      const id = currentLead().id;
      await saveAppointmentFields(form);
      await reloadDetail();
      const q = new URLSearchParams({ contact_id: String(state.form.contact_id ?? ""), caller: $<HTMLInputElement>("caller").value });
      const { text } = await api<{ text: string }>(`/api/leads/${id}/appointment?${q}`);
      void copy(text, "appointment details");
    } catch (e) { toast(errorMessage(e)); }
  });
}

function bindHeader(): void {
  const train = $<HTMLButtonElement>("train"), sync = $<HTMLButtonElement>("sync"), caller = $<HTMLInputElement>("caller");
  train.addEventListener("click", async () => {
    train.disabled = true;
    try { showModel(await api<ModelMetrics>("/api/train", {})); toast("AI trained"); await refresh(); }
    catch (e) { toast("Training failed: " + errorMessage(e)); }
    train.disabled = false;
  });
  sync.addEventListener("click", async () => {
    sync.disabled = true;
    try {
      const r = await api<SyncCounts>("/api/sync", {});
      toast("Synced: " + Object.entries(r).map(([t, n]) => `${t} ${n}`).join(", "));
    } catch (e) { toast("Sync failed: " + errorMessage(e)); }
    sync.disabled = false;
  });
  $("saveMainPhone").addEventListener("click", () => void patch({ phone: $<HTMLInputElement>("mainPhone").value }, "Main line saved"));
  caller.value = store("lumen.caller") ?? "";
  caller.addEventListener("change", () => store("lumen.caller", caller.value));
}

export function bindEvents(): void {
  document.addEventListener("keydown", onKeydown);
  bindLeadList(); bindLeadHeader(); bindContacts(); bindActivityLog(); bindDetails(); bindHeader();
}

async function saveAppointmentFields(form: HTMLFormElement): Promise<void> {
  const {contact_name,contact_title,contact_phone,contact_email,...lead} = Object.fromEntries(new FormData(form));
  try {
    if (state.form.contact_id) await api(`/api/contacts/${state.form.contact_id}`, {name:contact_name,title:contact_title,phone:contact_phone,email:contact_email});
    await api(`/api/leads/${currentLead().id}`,lead); await reloadDetail(); toast("Details saved");
  } catch(e) { toast(errorMessage(e)); throw e; }
}
