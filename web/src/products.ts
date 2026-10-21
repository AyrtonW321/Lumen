import { patch } from "./actions";
import { productChip } from "./format";
import { config, currentLead } from "./state";
import { $, esc } from "./util";

export function renderProducts(): void {
  const lead = currentLead(), container = $("lProducts");
  const focusedProduct = container.contains(document.activeElement) ? (document.activeElement as HTMLInputElement)?.dataset.product : undefined;
  const open = container.dataset.lead === String(lead.id) && !!container.querySelector<HTMLDetailsElement>("details")?.open;
  const products = lead.products.split(",");
  container.dataset.lead = String(lead.id);
  container.innerHTML = config().products.filter(p => products.includes(p)).map(productChip).join("")
    + `<details class="product-picker" ${open ? "open" : ""}><summary aria-label="Add or remove products" title="Add or remove products"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg></summary><fieldset><legend>Products</legend>${config().products.map(p => `<label><input type="checkbox" data-product="${esc(p)}" ${products.includes(p) ? "checked" : ""}>${esc(p)}</label>`).join("")}</fieldset></details>`;
  const menu = container.querySelector<HTMLDetailsElement>("details")!;
  const position = () => {
    if (!menu.open) return;
    const rect = menu.querySelector("summary")!.getBoundingClientRect(), fieldset = menu.querySelector("fieldset")!;
    fieldset.style.left = `${Math.max(8, Math.min(rect.left, innerWidth - 248))}px`;
    fieldset.style.top = `${Math.max(8, Math.min(rect.bottom + 8, innerHeight - fieldset.offsetHeight - 8))}px`;
  };
  menu.addEventListener("toggle", position);
  position();
  if (focusedProduct && open) [...menu.querySelectorAll<HTMLInputElement>("input")].find(i => i.dataset.product === focusedProduct)?.focus();
}

export function bindProducts(): void {
  const container = $("lProducts");
  container.addEventListener("change", async e => {
    const input = e.target as HTMLInputElement;
    const product = input.dataset.product;
    if (!product) return;
    const products = new Set(currentLead().products.split(",").filter(Boolean));
    if (input.checked) products.add(product); else products.delete(product);
    const menu = container.querySelector("fieldset")!;
    menu.disabled = true;
    await patch({ products: [...products] });
    // Also restores the saved values after a failed request.
    renderProducts();
  });
  container.addEventListener("keydown", e => {
    if (!((e.target as Element).closest(".product-picker"))) return;
    e.stopPropagation();
    if (e.key === "Escape") {
      e.preventDefault();
      container.querySelector<HTMLDetailsElement>("details")!.open = false;
      container.querySelector<HTMLElement>("summary")!.focus();
    }
  });
  document.addEventListener("click", e => {
    if (!container.contains(e.target as Node)) {
      const menu = container.querySelector<HTMLDetailsElement>("details");
      if (menu) menu.open = false;
    }
  });
  const close = () => { const menu = container.querySelector<HTMLDetailsElement>("details"); if (menu) menu.open = false; };
  window.addEventListener("resize", close);
  document.addEventListener("scroll", e => { if (!container.contains(e.target as Node)) close(); }, true);
}
