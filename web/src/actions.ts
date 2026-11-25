import { loadCallbacks } from "./callbacks";
import { fillDetails, renderList, renderPanel } from "./render";
import { config, currentLead, state } from "./state";
import type { LeadDetail, LeadRow } from "./types";
import { $, api, errorMessage, loadError, toast } from "./util";

export function resetContactForm(): void {
  state.editingContact = null; $<HTMLFormElement>("contactForm").reset();
  $("contactSave").textContent = "Add contact"; $("contactSummary").textContent = "+ Add contact";
}

export function resetForm(): void {
  state.form = { outcome: null, contact_id: state.detail?.contacts.at(-1)?.id ?? null };
  $<HTMLInputElement>("callback_date").value = ""; $<HTMLInputElement>("callback_time").value = ""; $<HTMLTextAreaElement>("note").value = "";
  $<HTMLInputElement>("expecting_call").checked = false; $<HTMLInputElement>("called_back").checked = false;
  renderPanel();
}

export function pickOutcome(code: string): void {
  state.form.outcome = code;
  if (code === "BKD") $<HTMLDetailsElement>("detailsBox").open = true;
}

export async function refresh(): Promise<void> {
  state.leads = await api<LeadRow[]>("/api/leads"); renderList(); renderPanel();
  await loadCallbacks();
}

const PANEL_SKELETON = `<div class="skel-panel" aria-busy="true" aria-label="Loading lead">${
  ["skel-head", "skel-short", "skel-card", "skel-tall", "skel-card", "skel-card"].map(c => `<div class="skel ${c}"></div>`).join("")}</div>`;
let loading = 0;

/** Shows the loading area in place of the lead panel. */
function panelLoad(): HTMLElement {
  const el = $("panelLoad");
  el.hidden = false; $("panel").hidden = true; $("empty").hidden = true;
  return el;
}

export async function select(id: number): Promise<void> {
  const ticket = ++loading;
  // Local loads are usually instant, so the skeleton only shows when one is slow.
  const timer = setTimeout(() => { panelLoad().innerHTML = PANEL_SKELETON; }, 150);
  try {
    const detail = await api<LeadDetail>(`/api/leads/${id}`);
    if (ticket !== loading) return;
    $("panelLoad").hidden = true;
    state.sel = id; state.detail = detail;
    resetContactForm(); fillDetails(); resetForm(); renderList();
  } catch {
    if (ticket !== loading) return;
    state.sel = null; state.detail = null; renderList();
    loadError(panelLoad(), "Couldn't load this lead. Is Lumen running?", () => void select(id));
  } finally { clearTimeout(timer); }
}

export function closeLead(): void {
  loading++; $("panelLoad").hidden = true;
  state.sel = null; state.detail = null; renderList(); renderPanel();
}

export async function reloadDetail(): Promise<void> {
  state.detail = await api<LeadDetail>(`/api/leads/${currentLead().id}`); await refresh();
}

export async function patch(fields: Record<string, unknown>, msg?: string): Promise<void> {
  try { await api(`/api/leads/${currentLead().id}`, fields); await reloadDetail(); if (msg) toast(msg); }
  catch (e) { toast(errorMessage(e)); }
}

export async function save(): Promise<void> {
  const { detail, form } = state;
  if (!detail || !form.outcome) return toast("Pick an outcome first");
  if (form.outcome === "CALLBACK" && !$<HTMLInputElement>("callback_date").value) return toast("Choose a callback date");
  if (form.outcome === "OTHER" && !$<HTMLTextAreaElement>("note").value.trim()) return toast("Describe what happened in the call log");
  const cfg = config();
  try {
    const r = await api<{ myphoner_comment: string }>("/api/activities", {
      lead_id: detail.id, outcome: form.outcome, contact_id: form.contact_id,
      callback_date: ["WIN", "LOST"].includes(form.outcome) ? null : $<HTMLInputElement>("callback_date").value || null,
      callback_time: ["WIN", "LOST"].includes(form.outcome) ? null : $<HTMLInputElement>("callback_time").value || null,
      expecting_call: form.outcome === "CALLBACK" && $<HTMLInputElement>("expecting_call").checked,
      called_back: $<HTMLInputElement>("called_back").checked,
      note: $<HTMLTextAreaElement>("note").value || null,
      caller: $<HTMLInputElement>("caller").value || null,
    });
    const moved = cfg.outcomes[form.outcome]?.move_to;
    try { await navigator.clipboard.writeText(r.myphoner_comment); toast(`Saved · copied for MyPhoner:\n${r.myphoner_comment}`); }
    catch { toast(`Saved · MyPhoner comment:\n${r.myphoner_comment}`); }
    if (moved) setTimeout(() => toast(`Moved to ${cfg.sources[moved]}`), 1500);
    await refresh(); await select(detail.id);
  } catch (e) { toast(errorMessage(e)); }
}
