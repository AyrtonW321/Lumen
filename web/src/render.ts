import { BRAND_VAR, PRODUCT_VAR, TABS } from "./constants";
import { brandChip, keyClass, leadRowClass, phoneText, pill, productChip, SMALL, tabClass } from "./format";
import { config, currentLead, state } from "./state";
import type { LeadRow, ModelMetrics, Product } from "./types";
import { $, esc, field } from "./util";

function sortKey(a: LeadRow, b: LeadRow): number {
  if (a.open !== b.open) return a.open ? -1 : 1;
  if (a.score != null || b.score != null) return (b.score ?? -1) - (a.score ?? -1);
  return a.tier - b.tier || (a.next_action_date ?? "").localeCompare(b.next_action_date ?? "") || a.name.localeCompare(b.name);
}

export function renderTabs(): void {
  const { leads, tab } = state;
  const count = (t: string) => t === "all" ? leads.length : leads.filter(l => l.source === t).length;
  $("tabs").innerHTML = TABS.map(([t, label]) =>
    `<button class="${tabClass(t, tab === t)}" data-tab="${t}"><b>${count(t)}</b>${label}</button>`).join("");
}

export function renderList(): void {
  renderTabs();
  const { leads, tab, sel } = state, cfg = config();
  const q = $<HTMLInputElement>("search").value.toLowerCase();
  const fb = $<HTMLSelectElement>("fBrand").value, fp = $<HTMLSelectElement>("fProduct").value;
  const listTab = tab === "new" || tab === "follow-up";
  state.view = leads.filter(l => (tab === "all" || l.source === tab) && l.name.toLowerCase().includes(q)
    && (!fb || l.brand === fb) && (!fp || l.products.split(",").includes(fp))
    && (!listTab || $<HTMLInputElement>("fClosed").checked || l.open)
    && (!$<HTMLInputElement>("fDue").checked || l.due)).sort(sortKey);
  $("sortNote").textContent = leads.some(l => l.score != null) ? "Sorted by AI score" : "Sorted by advice";
  $("list").innerHTML = state.view.map(l => `<div class="${leadRowClass(sel === l.id)}" data-id="${l.id}" style="--brand:var(${BRAND_VAR[l.brand]})">
    <div class="flex items-baseline justify-between gap-2"><span class="min-w-0 font-semibold wrap-anywhere">${esc(l.name)}</span>${l.score != null ? pill(l.score) : l.closed ? `<span class="chip">${l.closed}</span>` : ""}</div>
    <small class="${SMALL}">${brandChip(l.brand)} ${l.products ? (l.products.split(",") as Product[]).map(productChip).join(" ") : ""}
      ${tab === "all" ? `<span class="chip">${cfg.sources[l.source]}</span>` : ""}
      ${l.label ? `<span class="chip" style="--c:var(${l.label === "good" ? "--color-success" : "--color-danger"})">${l.label}</span>` : ""}
      · ${l.last_outcome ?? "not called"}${l.next_action_date && l.open ? " · next " + l.next_action_date : ""}</small>
    ${l.advice[0] ? `<small class="${SMALL} text-ink">${esc(l.advice[0])}</small>` : ""}</div>`).join("") || '<p class="hint">No leads here.</p>';
}

export function renderPanel(): void {
  const { detail, form, leads } = state;
  $("empty").hidden = !!detail; $("panel").hidden = !detail;
  if (!detail) return;
  const cfg = config();
  const row = leads.find(l => l.id === detail.id);
  $("head").style.setProperty("--brand", `var(${BRAND_VAR[detail.brand]})`);
  $("lName").textContent = detail.name;
  const sourceColor = detail.source === "winner" ? "--color-success" : detail.source === "loser" ? "--color-danger" : "--color-primary";
  $("lMeta").innerHTML = `${brandChip(detail.brand)} <span>${esc(cfg.brands[detail.brand])}</span>
    <span class="chip" style="--c:var(${sourceColor})">${cfg.sources[detail.source]}</span>
    <span>${detail.activities.length} touches · next call ${detail.next_action_date ?? "—"}</span>
    ${detail.phone ? `<span>📞 ${esc(detail.phone)} (B)</span><button class="btn-ghost btn-icon" data-copy="${esc(detail.phone)}" data-label="phone">📋</button>` : ""}
    ${detail.list_name ? `<span>· list ${esc(detail.list_name)}</span>` : ""}`;
  $<HTMLSelectElement>("lBrand").value = detail.brand; $<HTMLSelectElement>("lSource").value = detail.source;
  const prods = detail.products.split(",");
  $("lProducts").innerHTML = cfg.products.map(p => `<button data-p="${p}" style="${prods.includes(p) ? `background:var(${PRODUCT_VAR[p]});border-color:var(${PRODUCT_VAR[p]});color:#fff` : ""}">${prods.includes(p) ? "✓ " : "+ "}${p}</button>`).join("");
  $("good").classList.toggle("on", detail.label === "good"); $("poor").classList.toggle("on", detail.label === "poor");
  $("lScore").innerHTML = row?.score != null ? `${pill(row.score)} <span class="hint">chance the next touch goes well${row.why?.length ? " · " + row.why.map(esc).join(", ") : ""}</span>` : "";
  $("lAdvice").innerHTML = (row?.advice ?? []).map(a => `<li>${esc(a)}</li>`).join("") || "<li>No advice yet</li>";
  $("contacts").innerHTML = detail.contacts.map((c, i) => `<span class="${keyClass(form.contact_id === c.id, "flex-wrap")}" data-c="${c.id}">
      <b>${i + 1}</b>${esc(c.name)}${c.title ? " · " + esc(c.title) : ""}${c.prefers_email ? " ✉" : ""}
      ${c.phone ? `<span class="phone">📞 ${esc(phoneText(c))}</span><button class="btn-ghost btn-icon" data-copy="${esc(c.phone)}" data-label="phone">📋</button>` : ""}
      <button class="btn-ghost btn-icon" data-edit="${c.id}" title="Edit contact">✎</button></span>`).join("")
    + `<span class="${keyClass(form.contact_id == null)}" data-c=""><b>0</b>No contact / main line</span>`;
  $("outcomes").innerHTML = Object.entries(cfg.outcomes).map(([code, o]) => `<span class="${keyClass(form.outcome === code)}" data-o="${code}"><b>${o.key.toUpperCase()}</b>${o.label}</span>`).join("");
  renderPreview();
  const names = new Map(detail.contacts.map(c => [c.id, c.name]));
  $("history").innerHTML = detail.activities.map(a => `<tr><td>${a.timestamp.replace("T", " ").slice(0, 16)}</td><td><b>${a.outcome}</b></td><td>${esc(names.get(a.contact_id ?? -1))}</td><td>${esc(a.note)}</td></tr>`).join("") || '<tr><td colspan="4" class="hint">No activity yet</td></tr>';
}

export function fillDetails(): void {
  const detail = currentLead(), f = $<HTMLFormElement>("detailsForm");
  for (const k of ["address", "facility_size", "phone", "solar_reference", "lighting_reference", "meeting_type"] as const) {
    field(f, k).value = detail[k] ?? "";
  }
  field(f, "appt_at").value = (detail.appt_at ?? "").slice(0, 16);
}

// Mirrors myphoner_comment() in lumen/activities.py; the server builds the saved version.
function preview(): string {
  const { form, detail } = state;
  if (!form.outcome || !detail) return "";
  const c = detail.contacts.find(c => c.id === form.contact_id);
  const who = c && (c.title ? `${c.name} (${c.title})` : c.name), cb = $<HTMLInputElement>("callback_date").value;
  return [`${form.outcome} ${new Date().toTimeString().slice(0, 5)}`, who, cb && `call back ${cb}`, $<HTMLTextAreaElement>("note").value].filter(Boolean).join(" - ");
}

export function renderPreview(): void { $("preview").textContent = preview() || "MyPhoner comment preview"; }

export function showModel(m: ModelMetrics | null): void {
  $("modelInfo").textContent = !m ? "AI not trained yet"
    : `AI trained on ${m.examples} examples` + (m.val_examples ? ` · ${m.beats_baseline ? "beats" : "does NOT beat"} guessing the average` : "");
}
