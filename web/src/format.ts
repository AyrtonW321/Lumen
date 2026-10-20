import { BRAND_VAR, PRODUCT_VAR } from "./constants";
import { config } from "./state";
import type { Brand, Contact, Product, TabId } from "./types";
import { esc } from "./util";

export const brandChip = (b: Brand): string => `<span class="chip" style="--c:var(${BRAND_VAR[b]})">${b}</span>`;
export const productChip = (p: Product): string => `<span class="chip" style="--c:var(${PRODUCT_VAR[p]})">${p}</span>`;

export const pill = (score: number): string => {
  const tone = score >= .6 ? "bg-success" : score >= .3 ? "bg-accent" : "bg-slate-400";
  return `<span class="rounded-full px-2 py-0.5 text-xs font-bold whitespace-nowrap text-white ${tone}">${Math.round(score * 100)}%</span>`;
};

export const phoneText = (c: Contact): string =>
  [c.phone, c.ext && `ext ${c.ext}`, c.phone_type && `(${config().phone_types[c.phone_type]})`].filter(Boolean).join(" ");

export const keyClass = (on: boolean, extra = ""): string => `key ${extra} ${on ? "on" : ""}`;

const TAB = "flex w-full cursor-pointer items-center justify-between gap-2 rounded-xl border-0 bg-transparent px-3 py-2.5 text-left text-[13px] font-bold text-mute hover:bg-soft max-[900px]:w-auto [&>b]:rounded-full [&>b]:px-2 [&>b]:py-px [&>b]:text-xs [&>b]:font-bold";
const TAB_IDLE = "[&>b]:bg-soft [&>b]:text-mute";
const TAB_ACTIVE: Partial<Record<TabId, string>> = {
  winner: "bg-success/10 text-success shadow-[inset_3px_0_0_var(--color-success)] [&>b]:bg-success [&>b]:text-white",
  loser: "bg-danger/10 text-danger shadow-[inset_3px_0_0_var(--color-danger)] [&>b]:bg-danger [&>b]:text-white",
};
const TAB_ACTIVE_DEFAULT = "bg-primary/10 text-primary shadow-[inset_3px_0_0_var(--color-primary)] [&>b]:bg-primary [&>b]:text-white";
export const tabClass = (tab: TabId, active: boolean): string => `${TAB} ${active ? TAB_ACTIVE[tab] ?? TAB_ACTIVE_DEFAULT : TAB_IDLE}`;

const LEAD_ROW = "flex min-w-0 cursor-pointer items-start gap-3 rounded-xl p-2.5 hover:bg-soft";
const LEAD_ROW_SELECTED = "bg-primary/8 ring-1 ring-primary/30 ring-inset";
export const leadRowClass = (selected: boolean): string => `${LEAD_ROW} ${selected ? LEAD_ROW_SELECTED : ""}`;

/** Round initial in the lead's brand colour. Needs --brand set on an ancestor. */
export const avatar = (name: string): string =>
  `<span class="grid size-9 shrink-0 place-items-center rounded-full bg-[color-mix(in_srgb,var(--brand,var(--color-primary))_16%,white)] text-sm font-extrabold text-(--brand,var(--color-primary))">${esc(initial(name))}</span>`;
export const initial = (name: string): string => name.trim().charAt(0).toUpperCase();

export const SMALL = "mt-0.5 block wrap-anywhere text-mute";
export const QUICK_BUTTON = "border-[color-mix(in_srgb,var(--color-primary)_35%,white)] bg-[color-mix(in_srgb,var(--color-primary)_6%,white)] px-2.5 py-[5px] text-[13px] text-primary";
