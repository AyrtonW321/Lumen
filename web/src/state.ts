import type { CallForm, Config, LeadDetail, LeadRow, TabId } from "./types";

// Shared UI state. Modules read and write fields on this one object.
interface State {
  cfg: Config | null;          // /api/config, set once at startup
  leads: LeadRow[];            // /api/leads
  view: LeadRow[];             // leads after tab, search and filters
  sel: number | null;          // selected lead id
  detail: LeadDetail | null;   // /api/leads/:id for the selected lead
  form: CallForm;              // the call being logged
  tab: TabId;
  editingContact: number | null; // contact id being edited, or null when adding
}

export const state: State = {
  cfg: null,
  leads: [],
  view: [],
  sel: null,
  detail: null,
  form: { outcome: null, contact_id: null },
  tab: "new",
  editingContact: null,
};

/** Config is loaded before anything renders, so the null case is a bug. */
export function config(): Config {
  if (!state.cfg) throw new Error("config not loaded");
  return state.cfg;
}

/** The lead panel is only reachable with a lead selected. */
export function currentLead(): LeadDetail {
  if (!state.detail) throw new Error("no lead selected");
  return state.detail;
}
