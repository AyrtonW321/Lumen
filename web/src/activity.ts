import { patch, pickOutcome, save } from "./actions";
import { QUICK, type QuickKind } from "./constants";
import { quickDate } from "./dates";
import { renderPanel, renderPreview } from "./render";
import { currentLead, state } from "./state";
import { $, toast } from "./util";

export const isClassification = (code: string | null): boolean => ["WIN", "LOST", "CALLBACK"].includes(code ?? "");

export function renderActivity(): void {
  const outcome = state.form.outcome;
  for (const [id, code] of [["regularCall", null], ["winner", "WIN"], ["loser", "LOST"], ["callback", "CALLBACK"]] as const) {
    const active = code ? outcome === code : !isClassification(outcome);
    $(id).setAttribute("aria-pressed", String(active));
  }
  $("outcomeField").hidden = isClassification(outcome);
  const closed = outcome === "WIN" || outcome === "LOST";
  $("callbackFields").hidden = closed;
  $("classificationHint").textContent = closed
    ? `Save call to record this ${outcome === "WIN" ? "winner" : "loser"} classification with your note. No contact result is needed.`
    : outcome === "CALLBACK" ? "Save call to schedule a callback and move this lead to Follow-ups, including previously won or lost leads."
    : "Choose a contact result, or classify the lead and describe what happened below.";
}

export function bindActivityLog(): void {
  for (const [id, code] of [["regularCall", null], ["winner", "WIN"], ["loser", "LOST"], ["callback", "CALLBACK"]] as const) {
    $(id).addEventListener("click", () => {
      state.form.outcome = code;
      if (code === "CALLBACK" && !$<HTMLInputElement>("callback_date").value) $<HTMLInputElement>("callback_date").value = quickDate("1d");
      renderPanel();
    });
  }
  $("outcomes").addEventListener("change", e => {
    const value = (e.target as HTMLSelectElement).value;
    state.form.outcome = value || null;
    if (value) pickOutcome(value);
    renderPanel();
  });
  $("quick").innerHTML = '<option value="">Quick callback date</option>' + QUICK.map(([k,l]) => `<option value="${k}">${l}</option>`).join("");
  $("quick").addEventListener("change", e => {
    const el = e.target as HTMLSelectElement;
    if (el.value) { $<HTMLInputElement>("callback_date").value = quickDate(el.value as QuickKind); el.value = ""; renderPreview(); }
  });
  $("reschedule").addEventListener("click", () => {
    const date = $<HTMLInputElement>("callback_date").value;
    if (!date) return toast("Pick a callback date first");
    const lead = currentLead();
    void patch({ next_action_date: date, ...(["winner", "loser"].includes(lead.source) ? {source:"follow-up"} : {}) }, `Next call set to ${date}`);
  });
  for (const id of ["callback_date", "note"]) $(id).addEventListener("input", renderPreview);
  $("save").addEventListener("click", () => void save());
}
