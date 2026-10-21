import { TABS } from "./constants";
import { productChip, tabClass } from "./format";
import { companyTag } from "./company-editor";
import { config, state } from "./state";
import type { LeadRow, Product } from "./types";
import { $, esc } from "./util";
function sortKey(a: LeadRow, b: LeadRow): number {
  if (a.open !== b.open) return a.open ? -1 : 1;
  if (a.score != null || b.score != null) return (b.score ?? -1) - (a.score ?? -1);
  return a.tier - b.tier || (a.next_action_date ?? "").localeCompare(b.next_action_date ?? "") || a.name.localeCompare(b.name);
}

function solutionTags(products: string): string {
  const values = products.split(",").filter(Boolean) as Product[];
  const extra = values.slice(2);
  return values.slice(0, 2).map(productChip).join(" ")
    + (extra.length ? `<span class="chip more-products" title="${esc(extra.join(", "))}" aria-label="${extra.length} more solutions: ${esc(extra.join(", "))}">+${extra.length}</span>` : "");
}

export function renderTabs(): void {
  const { leads, tab } = state;
  const count = (t: string) => t === "all" ? leads.length : leads.filter(l => l.source === t).length;
  $("tabs").innerHTML = TABS.map(([t, label]) =>
    `<button class="${tabClass(t, tab === t)}" data-tab="${t}"><span>${label}</span><b>${count(t)}</b></button>`).join("");
}

export function renderList(): void {
  renderTabs();
  const { leads, tab, sel } = state, cfg = config();
  const q = $<HTMLInputElement>("search").value.toLowerCase();
  const fb = $<HTMLSelectElement>("fBrand").value;
  const products = [...$("fProduct").querySelectorAll<HTMLInputElement>("input:checked")].map(i => i.value);
  const status = $<HTMLSelectElement>("fStatus").value, quality = $<HTMLSelectElement>("fQuality").value;
  state.view = leads.filter(l => (tab === "all" || l.source === tab) && l.name.toLowerCase().includes(q)
    && (!fb || l.brand === fb) && (!products.length || products.some(p => l.products.split(",").includes(p)))
    && (!status || (status === "closed" ? !!l.closed : l.source === status))
    && (!quality || (quality === "unrated" ? !l.label : l.label === quality))
    && (!$<HTMLInputElement>("fDue").checked || l.due)).sort(sortKey);
  $("sortNote").hidden = !leads.some(l => l.score != null);
  $("sortNote").textContent = "Open leads ranked by predicted call success";
  $("list").innerHTML = state.view.map(l => `<article tabindex="0" class="lead-row ${sel === l.id ? 'selected' : ''}" data-id="${l.id}" aria-label="${esc(l.name)}" ${sel === l.id ? 'aria-current="true"' : ''}>
    <div class="lead-heading"><div class="lead-identity"><div class="lead-title">${esc(l.name)}</div><div class="lead-tags">${companyTag(l.brand, l.id)} ${solutionTags(l.products)}</div></div><span class="status status-${l.source}">${esc(cfg.sources[l.source])}</span></div>
    <div class="lead-classification">${l.list_name ? `<span class="list-origin">List: ${esc(l.list_name)}</span>` : ""}${l.label ? `<span class="quality quality-${l.label}">${l.label === "good" ? "Good lead" : "Poor lead"}</span>` : ""}${l.closed ? `<span class="hint">Closed · ${esc(cfg.outcomes[l.closed]?.label ?? l.closed)}</span>` : ""}</div>
    <div class="last-contacted">Last contacted: ${l.last_contacted ? esc(l.last_contacted.replace("T", " ").slice(0,16)) : "Never"}</div>
    <div class="last-result"><strong>${l.last_outcome ? esc(cfg.outcomes[l.last_outcome]?.label ?? l.last_outcome) : "No calls recorded"}</strong>${l.next_action_date && l.open ? `<span>Next call · ${esc(l.next_action_date)}</span>` : ""}</div>
  </article>`).join("") || '<p class="hint">No leads match these filters.</p>';
}

