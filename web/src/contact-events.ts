import { reloadDetail, resetContactForm } from "./actions";
import { renderPanel } from "./render";
import { currentLead, state } from "./state";
import { $, api, errorMessage, field, toast } from "./util";
const closest = (e: Event, selector: string): HTMLElement | null => (e.target as Element).closest<HTMLElement>(selector);
export function bindContacts(): void {
  $("contacts").addEventListener("click", e => {
    if (closest(e, "[data-copy]")) return;
    const move = closest(e, "[data-move]");
    if (move) { void moveContact(Number(move.dataset.move), Number(move.dataset.direction)); return; }
    const ed = closest(e, "[data-edit]");
    if (ed) {
      const c = currentLead().contacts.find(c => c.id === Number(ed.dataset.edit)), f = $<HTMLFormElement>("contactForm");
      if (!c) return;
      for (const k of ["name", "title", "phone", "ext", "phone_type", "email", "status"] as const) field(f, k).value = c[k] ?? "";
      state.editingContact = c.id; $("contactSave").textContent = "Save contact"; $("contactSummary").textContent = `Edit ${c.name}`;
      $<HTMLDetailsElement>("contactBox").open = true;
      return;
    }
    const el = closest(e, "[data-c]");
    if (el) { state.form.contact_id = el.dataset.c ? Number(el.dataset.c) : null; renderPanel(); }
  });
  const form = $<HTMLFormElement>("contactForm");
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(form));
    try {
      if (state.editingContact) { await api(`/api/contacts/${state.editingContact}`, body); toast("Contact saved"); }
      else { state.form.contact_id = (await api<{ id: number }>(`/api/leads/${currentLead().id}/contacts`, body)).id; }
      resetContactForm();
      await reloadDetail();
    } catch (err) { toast(errorMessage(err)); }
  });
}

async function moveContact(id: number, direction: number): Promise<void> {
  const contacts = [...currentLead().contacts]; const index = contacts.findIndex(c => c.id === id), next = index + direction;
  if (index < 0 || next < 0 || next >= contacts.length) return;
  [contacts[index], contacts[next]] = [contacts[next]!, contacts[index]!];
  try { for (const [order,c] of contacts.entries()) await api(`/api/contacts/${c.id}`, {sort_order:order}); await reloadDetail(); }
  catch (e) { toast(errorMessage(e)); }
}
