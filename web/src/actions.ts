import { fillDetails, renderList, renderPanel } from "./render";
import { config, currentLead, state } from "./state";
import type { LeadDetail, LeadRow } from "./types";
import { $, api, errorMessage, toast } from "./util";

export function resetContactForm(): void {
  state.editingContact = null; $<HTMLFormElement>("contactForm").reset();
  $("contactSave").textContent = "Add contact"; $("contactSummary").textContent = "+ Add contact";
}

export function resetForm(): void {
  state.form = { outcome: null, contact_id: state.detail?.contacts.at(-1)?.id ?? null };
  $<HTMLInputElement>("callback_date").value = ""; $<HTMLTextAreaElement>("note").value = "";
  renderPanel();
}

export function pickOutcome(code: string): void {
  state.form.outcome = code;
  if (code === "BKD") $<HTMLDetailsElement>("detailsBox").open = true;
}

export async function refresh(): Promise<void> {
  state.leads = await api<LeadRow[]>("/api/leads"); renderList(); renderPanel();
}

export async function select(id: number): Promise<void> {
  state.sel = id; state.detail = await api<LeadDetail>(`/api/leads/${id}`);
  resetContactForm(); fillDetails(); resetForm(); renderList();
}

export function closeLead(): void { state.sel = null; state.detail = null; renderList(); renderPanel(); }

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
  if (form.outcome === "OTHER" && !$<HTMLTextAreaElement>("note").value.trim()) return toast("Describe what happened in the call log");
  const cfg = config();
  try {
    const r = await api<{ myphoner_comment: string }>("/api/activities", {
      lead_id: detail.id, outcome: form.outcome, contact_id: form.contact_id,
      callback_date: $<HTMLInputElement>("callback_date").value || null,
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
