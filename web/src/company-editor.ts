import { refresh, reloadDetail } from "./actions";
import { BRAND_VAR } from "./constants";
import { config, state } from "./state";
import type { Brand } from "./types";
import { api, errorMessage, esc, toast } from "./util";

export function companyTag(brand: Brand, leadId: number): string {
  return `<button type="button" class="chip company-tag" data-company-lead="${leadId}" style="--c:var(${BRAND_VAR[brand]})" aria-label="Change company: ${brand}" aria-haspopup="dialog">${brand}</button>`;
}

export function bindCompanyEditor(): void {
  const editor = document.createElement("div");
  editor.className = "company-editor";
  editor.setAttribute("role", "dialog");
  editor.setAttribute("aria-label", "Change lead company");
  editor.hidden = true;
  document.body.append(editor);
  let trigger: HTMLElement | null = null;
  let leadId: number | null = null;
  const close = (restoreFocus = false) => {
    editor.hidden = true;
    if (restoreFocus) {
      const replacement = document.querySelector<HTMLElement>(`[data-company-lead="${leadId}"]`);
      (trigger?.isConnected ? trigger : replacement)?.focus();
    }
  };
  document.addEventListener("click", e => {
    const target = e.target as Element;
    const tag = target.closest<HTMLElement>("[data-company-lead]");
    if (!tag) { if (!editor.contains(target)) close(); return; }
    trigger = tag;
    leadId = Number(tag.dataset.companyLead);
    const lead = state.leads.find(l => l.id === leadId) ?? state.detail;
    if (!lead) return;
    editor.innerHTML = `<form><label>Company<select name="company" aria-label="Company assignment">${Object.entries(config().brands).map(([brand, region]) => `<option value="${brand}" ${brand === lead.brand ? "selected" : ""}>${brand} (${esc(region)})</option>`).join("")}</select></label><div><button type="submit" class="btn-primary">Save</button><button type="button" data-cancel>Cancel</button></div></form>`;
    editor.hidden = false;
    const rect = tag.getBoundingClientRect();
    editor.style.left = `${Math.max(8, Math.min(rect.left, innerWidth - 268))}px`;
    editor.style.top = `${Math.max(8, Math.min(rect.bottom + 8, innerHeight - editor.offsetHeight - 8))}px`;
    editor.querySelector("select")?.focus();
  });
  editor.addEventListener("click", e => { if ((e.target as Element).closest("[data-cancel]")) close(true); });
  editor.addEventListener("keydown", e => {
    e.stopPropagation();
    if (e.key === "Escape") { e.preventDefault(); close(true); }
  });
  editor.addEventListener("submit", async e => {
    e.preventDefault();
    const id = leadId;
    if (id == null) return;
    const company = editor.querySelector("select")!.value;
    const save = editor.querySelector<HTMLButtonElement>("[type=submit]")!;
    save.disabled = true;
    try {
      await api(`/api/leads/${id}`, { brand: company });
      if (state.detail?.id === id) await reloadDetail(); else await refresh();
      close(true);
      toast("Company updated");
    } catch (error) { toast(errorMessage(error)); }
    finally { save.disabled = false; }
  });
  window.addEventListener("resize", () => close());
  document.addEventListener("scroll", () => close(), true);
}
