/** Get an element by id. Throws if it is missing, so a typo in index.html fails loudly. */
export function $<T extends HTMLElement = HTMLElement>(id: string): T {
  const el = document.getElementById(id);
  if (!el) throw new Error(`missing #${id}`);
  return el as T;
}

const ESCAPES: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" };
export const esc = (s: unknown): string => String(s ?? "").replace(/[&<>"]/g, c => ESCAPES[c] ?? c);

export async function api<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error);
  return json as T;
}

/** Message of anything thrown. */
export const errorMessage = (e: unknown): string => e instanceof Error ? e.message : String(e);

// localStorage can throw (private mode, blocked), so failures are ignored.
export function store(key: string): string | null;
export function store(key: string, value: string): void;
export function store(key: string, value?: string): string | null | void {
  try { return value === undefined ? localStorage.getItem(key) : localStorage.setItem(key, value); }
  catch { return value === undefined ? null : undefined; }
}

let toastTimer: number | undefined;
export function toast(msg: string): void {
  const el = $("toast");
  el.textContent = msg; el.classList.replace("opacity-0", "opacity-100");
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => el.classList.replace("opacity-100", "opacity-0"), 3000);
}

export async function copy(text: string, label: string): Promise<void> {
  try { await navigator.clipboard.writeText(text); toast(`Copied ${label}`); }
  catch { toast(`Copy blocked. ${label}:\n${text}`); }
}

export function options(el: HTMLElement, entries: ReadonlyArray<readonly [string, string]>, first?: string): void {
  el.innerHTML = (first != null ? `<option value="">${first}</option>` : "")
    + entries.map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join("");
}

/** Named form control, typed. */
export function field(form: HTMLFormElement, name: string): HTMLInputElement {
  return form.elements.namedItem(name) as HTMLInputElement;
}
