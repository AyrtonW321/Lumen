export { renderList, renderTabs } from "./directory";
import { isClassification, renderActivity } from "./activity";
import { icon } from "./icons";
import { BRAND_VAR } from "./constants";
import { phoneText, pill } from "./format";
import { companyTag } from "./company-editor";
import { renderProducts } from "./products";
import { config, currentLead, state } from "./state";
import type { ModelMetrics } from "./types";
import { $, esc, field } from "./util";

export function renderPanel(): void {
  const { detail, form, leads } = state;
  $("empty").hidden = !!detail; $("panel").hidden = !detail;
  if (!detail) return;
  const cfg = config();
  const row = leads.find(l => l.id === detail.id);
  $("head").style.setProperty("--brand", `var(${BRAND_VAR[detail.brand]})`);
  $("lName").textContent = detail.name;
  $("lCompanyTag").innerHTML = companyTag(detail.brand, detail.id);
  const sourceColor = detail.source === "winner" ? "--color-success" : detail.source === "loser" ? "--color-danger" : "--color-primary";
  $("lMeta").innerHTML = `<div class="detail-identity"><span>${esc(cfg.brands[detail.brand])}</span><span class="chip" style="--c:var(${sourceColor})">${cfg.sources[detail.source]}</span></div>
    <dl class="lead-facts"><div><dt>Last contacted</dt><dd>${esc(detail.activities[0]?.timestamp.replace("T", " ").slice(0, 16) ?? "Never")}</dd></div><div><dt>Next call</dt><dd>${esc(detail.next_action_date ?? "Not scheduled")}</dd></div><div><dt>Calls logged</dt><dd>${detail.activities.length}</dd></div>
    ${detail.phone ? `<div><dt>Main line</dt><dd>${esc(detail.phone)} <button class="btn-ghost btn-icon" data-copy="${esc(detail.phone)}" data-label="phone" aria-label="Copy main phone">${icon("copy")}</button></dd></div>` : ""}
    ${detail.list_name ? `<div><dt>List</dt><dd>${esc(detail.list_name)}</dd></div>` : ""}</dl>`;
  $<HTMLSelectElement>("lBrand").value = detail.brand; $<HTMLSelectElement>("lSource").value = detail.source;
  renderProducts();
  $("good").classList.toggle("on", detail.label === "good"); $("poor").classList.toggle("on", detail.label === "poor");
  $("lScore").innerHTML = row?.score != null ? `${pill(row.score)} <span class="hint">chance the next touch goes well${row.why?.length ? " · " + row.why.map(esc).join(", ") : ""}</span>` : "";
  $("lAdvice").innerHTML = (row?.advice ?? []).map(a => `<li>${esc(a)}</li>`).join("") || "<li>No advice yet</li>";
  $("mainPhone").setAttribute("placeholder", detail.phone || "Company phone number");
  if (document.activeElement?.id !== "mainPhone") $<HTMLInputElement>("mainPhone").value = detail.phone ?? "";
  $("contacts").innerHTML = detail.contacts.map((c, i) => `<div class="contact-row ${form.contact_id === c.id ? "contact-selected" : ""}">
    <button type="button" class="contact-pick" data-c="${c.id}" aria-pressed="${form.contact_id === c.id}"><span class="contact-identity"><strong>${esc(c.name)}</strong><span class="contact-title">${esc(c.title || "No position added")}</span></span><span class="contact-reach"><span class="contact-phone">${esc(phoneText(c)) || "No phone added"}</span><span class="contact-status" data-status="${esc(c.status ?? "")}">${esc(c.status?.replaceAll("-", " ") || "Unclassified")}</span></span></button>
    <div class="contact-actions">${c.phone ? `<button class="btn-icon" data-copy="${esc(c.phone)}" data-label="phone" aria-label="Copy phone">${icon("copy")}</button>` : ""}<button class="btn-icon" data-edit="${c.id}" aria-label="Edit ${esc(c.name)}">${icon("edit")}</button><button class="btn-icon" data-move="${c.id}" data-direction="-1" aria-label="Move ${esc(c.name)} up" ${i === 0 ? "disabled" : ""}>${icon("up")}</button><button class="btn-icon" data-move="${c.id}" data-direction="1" aria-label="Move ${esc(c.name)} down" ${i === detail.contacts.length - 1 ? "disabled" : ""}>${icon("down")}</button></div></div>`).join("")
    + `<button type="button" class="mainline ${form.contact_id == null ? "on" : ""}" data-c="">Use main line ${esc(detail.phone ?? "— add a default number below")}</button>`;
  $("outcomes").innerHTML = `<option value="">Select a call result</option>` + Object.entries(cfg.outcomes).filter(([code]) => !isClassification(code)).map(([code,o]) => `<option value="${code}" ${form.outcome === code ? "selected" : ""}>${esc(o.label)}</option>`).join("");
  renderActivity();
  fillContactDetails();
  renderPreview();
  const names = new Map(detail.contacts.map(c => [c.id, c.name]));
  $("history").innerHTML = detail.activities.map(a => `<tr><td>${a.timestamp.replace("T", " ").slice(0, 16)}</td><td><b>${esc(cfg.outcomes[a.outcome]?.label ?? a.outcome)}</b></td><td>${esc(names.get(a.contact_id ?? -1))}</td><td class="history-note">${esc(a.note)}</td></tr>`).join("") || '<tr><td colspan="4" class="hint">No activity yet</td></tr>';
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
  const who = c && (c.title ? `${c.name} (${c.title})` : c.name), cb = ["WIN", "LOST"].includes(form.outcome) ? "" : $<HTMLInputElement>("callback_date").value;
  return [`${form.outcome} ${new Date().toTimeString().slice(0, 5)}`, who, cb && `call back ${cb}`, $<HTMLTextAreaElement>("note").value].filter(Boolean).join(" - ");
}

export function renderPreview(): void { $("preview").textContent = preview() || "MyPhoner comment preview"; }

export function showModel(m: ModelMetrics | null): void {
  $("modelInfo").textContent = !m ? "AI not trained yet"
    : `AI trained on ${m.examples} examples` + (m.val_examples ? ` · ${m.beats_baseline ? "beats" : "does NOT beat"} guessing the average` : "");
}

export function fillContactDetails(): void {
  const c = state.detail?.contacts.find(c => c.id === state.form.contact_id);
  const f = $<HTMLFormElement>("detailsForm");
  for (const [name,value] of Object.entries({contact_name:c?.name,contact_title:c?.title,contact_phone:c?.phone,contact_email:c?.email})) field(f,name).value = value ?? "";
}
