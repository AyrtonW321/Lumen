import { reloadDetail } from "./actions";
import { renderList } from "./directory";
import { config, currentLead, state } from "./state";
import type { LeadRow, Trait, TraitCatalog, TraitChip } from "./types";
import { $, api, errorMessage, esc, toast } from "./util";

export const AUTO_BADGES = ["Responsive", "Hard to reach", "Doesn't call back"];

const isWarning = (name: string): boolean => (config().warning_traits ?? []).includes(name);

/** One chip. Warnings get the danger colour, automatic badges a dashed outline. */
export function traitChip(name: string, note?: string | null, opts: { auto?: boolean; edit?: number; full?: boolean } = {}): string {
  const cls = `chip trait-chip${isWarning(name) ? " trait-warn" : ""}${opts.auto ? " trait-auto" : ""}`;
  const body = `${esc(name)}${opts.full && note ? `<span class="trait-note"> · ${esc(note)}</span>` : ""}`;
  const title = note ? ` title="${esc(note)}"` : opts.auto ? ' title="Worked out from call history"' : "";
  return opts.edit != null
    ? `<button type="button" class="${cls}" data-trait-edit="${opts.edit}"${title} aria-label="Edit trait ${esc(name)}">${body}</button>`
    : `<span class="${cls}"${title}>${body}</span>`;
}

/** Up to `max` chips for compact rows, warnings first. */
export function compactChips(traits: TraitChip[] = [], badges: string[] = [], max = 3): string {
  const seen = new Set<string>();
  const all = [...badges.map(name => ({ name, note: null, auto: true })), ...traits.map(t => ({ ...t, auto: false }))]
    .filter(t => !seen.has(t.name) && seen.add(t.name));
  all.sort((a, b) => Number(isWarning(b.name)) - Number(isWarning(a.name)));
  const shown = all.slice(0, max), extra = all.length - shown.length;
  return shown.map(t => traitChip(t.name, t.note, { auto: t.auto })).join("")
    + (extra > 0 ? `<span class="chip more-traits" title="${esc(all.slice(max).map(t => t.name).join(", "))}">+${extra}</span>` : "");
}

/** Strip at the top of the lead panel: company traits, badges, and every concern note on the lead. */
export function renderHeadsUp(): void {
  const lead = currentLead();
  const concerns = lead.contacts.flatMap(c => (c.traits ?? []).filter(t => t.note && isWarning(t.name)).map(t => ({ c, t })));
  $("headsUp").innerHTML = `<div class="heads-up-row"><strong>Heads-up</strong>
    ${(lead.badges ?? []).map(b => traitChip(b, null, { auto: true })).join("")}
    ${(lead.traits ?? []).map(t => traitChip(t.name, t.note, { edit: t.id, full: true })).join("")}
    <button type="button" class="btn-ghost trait-add" data-trait-add="">+ Company trait</button></div>
    ${concerns.length ? `<ul class="heads-up-notes">${concerns.map(({ c, t }) => `<li><b>${esc(c.name)}</b> · ${esc(t.name)}: ${esc(t.note)}</li>`).join("")}</ul>` : ""}`;
}

/** Chips shown on a contact card. */
export function contactChips(traits: Trait[] = [], badges: string[] = []): string {
  return badges.map(b => traitChip(b, null, { auto: true })).join("") + traits.map(t => traitChip(t.name, t.note, { edit: t.id, full: true })).join("");
}

// ---- filter ----

/** True when the lead has the trait. Person traits match if any contact has them. */
function hasTrait(l: LeadRow, key: string): boolean {
  const [scope, name] = [key.slice(0, key.indexOf(":")), key.slice(key.indexOf(":") + 1)];
  if (scope === "auto") return (l.badges ?? []).includes(name);
  return (l.traits ?? []).some(t => t.person === (scope === "person") && t.name.toLowerCase() === name.toLowerCase());
}

export function matchesTraits(l: LeadRow): boolean {
  for (const [key, mode] of state.traitFilter) if (hasTrait(l, key) !== (mode === "in")) return false;
  return true;
}

export const traitText = (l: LeadRow): string => (l.traits ?? []).map(t => `${t.name} ${t.note ?? ""}`).join(" ").toLowerCase();

export function renderTraitFilter(): void {
  const groups: Array<[string, string, string[]]> = [
    ["person", "Person", state.catalog.person], ["company", "Company", state.catalog.company], ["auto", "Auto", AUTO_BADGES]];
  $("fTraits").innerHTML = groups.map(([scope, label, names]) => `<div class="trait-group"><span>${label}</span><div>${names.map(n => {
    const key = `${scope}:${n}`, mode = state.traitFilter.get(key);
    const said = mode === "in" ? "must have" : mode === "out" ? "must not have" : "any";
    return `<button type="button" class="trait-toggle" data-trait-filter="${esc(key)}" data-mode="${mode ?? ""}" aria-label="${esc(n)}: ${said}">${mode === "out" ? "not " : ""}${esc(n)}</button>`;
  }).join("")}</div></div>`).join("");
}

export async function loadCatalog(): Promise<void> {
  state.catalog = await api<TraitCatalog>("/api/traits");
  renderTraitFilter();
}

// ---- picker ----

interface Target { leadId: number; contactId: number | null; trait: Trait | null; }
let target: Target | null = null;

function pickerHtml(t: Target): string {
  const lead = currentLead();
  const who = t.contactId ? lead.contacts.find(c => c.id === t.contactId)?.name ?? "contact" : lead.name;
  const names = t.contactId ? state.catalog.person : state.catalog.company;
  const editing = t.trait;
  return `<form class="trait-form" autocomplete="off">
    <h4>${editing ? `Edit ${esc(editing.name)}` : `Add trait · ${esc(who)}`}</h4>
    ${editing ? "" : `<div class="trait-presets">${names.map(n => `<button type="button" class="chip trait-chip${isWarning(n) ? " trait-warn" : ""}" data-trait-pick="${esc(n)}">${esc(n)}</button>`).join("")}</div>
    <label>Trait<input name="name" maxlength="40" required placeholder="Pick above or type a new one"></label>
    <label class="trait-save"><input type="checkbox" name="save"> Save for reuse (adds it to the picker and filter)</label>`}
    <label>Note (optional)<input name="note" maxlength="200" value="${esc(editing?.note ?? "")}" placeholder="e.g. worried about upfront cost"></label>
    ${editing && !editing.global ? `<label class="trait-save"><input type="checkbox" name="promote"> Save for reuse</label>` : ""}
    <p class="hint">Keep notes about the business conversation, not personal details.</p>
    <div class="trait-buttons"><button type="submit" class="btn-primary">Save</button>${editing ? '<button type="button" class="btn-danger" data-trait-remove>Remove</button>' : ""}<button type="button" data-trait-cancel>Cancel</button></div>
  </form>`;
}

export function bindTraits(): void {
  const box = document.createElement("div");
  box.className = "trait-editor"; box.id = "traitEditor";
  box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Trait"); box.hidden = true;
  document.body.append(box);
  const close = () => { box.hidden = true; target = null; };
  const known = () => new Set((target?.contactId ? state.catalog.person : state.catalog.company).map(n => n.toLowerCase()));

  document.addEventListener("click", e => {
    const el = e.target as Element;
    const add = el.closest<HTMLElement>("[data-trait-add]"), edit = el.closest<HTMLElement>("[data-trait-edit]");
    if (!add && !edit) { if (!box.contains(el)) close(); return; }
    e.stopPropagation();
    const lead = currentLead();
    let trait: Trait | null = null;
    if (edit) {
      const id = Number(edit.dataset.traitEdit);
      trait = [...(lead.traits ?? []), ...lead.contacts.flatMap(c => c.traits ?? [])].find(t => t.id === id) ?? null;
      if (!trait) return;
    }
    const contactId = trait ? trait.contact_id : add!.dataset.traitAdd ? Number(add!.dataset.traitAdd) : null;
    target = { leadId: lead.id, contactId, trait };
    box.innerHTML = pickerHtml(target); box.hidden = false;
    const rect = (add ?? edit)!.getBoundingClientRect();
    box.style.left = `${Math.max(8, Math.min(rect.left, innerWidth - 348))}px`;
    box.style.top = `${Math.max(8, Math.min(rect.bottom + 8, innerHeight - box.offsetHeight - 8))}px`;
    box.querySelector<HTMLInputElement>("input")?.focus();
  });
  box.addEventListener("click", e => {
    const el = e.target as Element, pick = el.closest<HTMLElement>("[data-trait-pick]");
    if (pick) {
      const input = box.querySelector<HTMLInputElement>("[name=name]")!;
      input.value = pick.dataset.traitPick ?? ""; input.dispatchEvent(new Event("input", { bubbles: true }));
      box.querySelector<HTMLInputElement>("[name=note]")?.focus();
    }
    if (el.closest("[data-trait-cancel]")) close();
    if (el.closest("[data-trait-remove]") && target?.trait) void run(api(`/api/traits/${target.trait.id}/delete`, {}), "Trait removed");
  });
  // A name already in the catalog is reused as is, so "save for reuse" does not apply.
  box.addEventListener("input", e => {
    if ((e.target as HTMLInputElement).name !== "name") return;
    const save = box.querySelector<HTMLInputElement>("[name=save]");
    if (save) save.disabled = known().has((e.target as HTMLInputElement).value.trim().toLowerCase());
  });
  box.addEventListener("keydown", e => { e.stopPropagation(); if (e.key === "Escape") { e.preventDefault(); close(); } });
  box.addEventListener("submit", e => {
    e.preventDefault();
    if (!target) return;
    const f = new FormData(box.querySelector("form")!), note = String(f.get("note") ?? "");
    if (target.trait) {
      void run(api(`/api/traits/${target.trait.id}`, { note, ...(f.get("promote") ? { global: true } : {}) }), "Trait saved");
    } else {
      void run(api("/api/traits", { lead_id: target.leadId, contact_id: target.contactId, name: f.get("name"), note, save: !!f.get("save") }), "Trait added");
    }
  });

  async function run(request: Promise<unknown>, msg: string): Promise<void> {
    try { await request; close(); await loadCatalog(); await reloadDetail(); toast(msg); }
    catch (err) { toast(errorMessage(err)); }
  }

  $("fTraits").addEventListener("click", e => {
    const b = (e.target as Element).closest<HTMLElement>("[data-trait-filter]");
    if (!b) return;
    const key = b.dataset.traitFilter!, mode = state.traitFilter.get(key);
    if (!mode) state.traitFilter.set(key, "in"); else if (mode === "in") state.traitFilter.set(key, "out"); else state.traitFilter.delete(key);
    renderTraitFilter(); renderList();
  });
  window.addEventListener("resize", close);
}
