import { BRAND_VAR, PRODUCT_VAR } from "./constants";
import { config } from "./state";
import type { Brand, Contact, Product, TabId } from "./types";

export const brandChip = (b: Brand): string => `<span class="chip" style="--c:var(${BRAND_VAR[b]})">${b}</span>`;
export const productChip = (p: Product): string => `<span class="chip" style="--c:var(${PRODUCT_VAR[p]})">${p}</span>`;

export const pill = (score: number): string => {
  const tone = score >= .6 ? "bg-success" : score >= .3 ? "bg-accent" : "bg-slate-400";
  return `<span class="rounded-full px-2 py-0.5 text-xs font-bold whitespace-nowrap text-white ${tone}">${Math.round(score * 100)}%</span>`;
};

export const phoneText = (c: Contact): string =>
  [c.phone, c.ext && `ext ${c.ext}`, c.phone_type && `(${config().phone_types[c.phone_type]})`].filter(Boolean).join(" ");

export const keyClass = (on: boolean, extra = ""): string => `key ${extra} ${on ? "on" : ""}`;

const TAB = "cursor-pointer truncate rounded-[7px] border-0 bg-transparent px-0.5 py-1.5 text-xs font-semibold text-mute [&>b]:block [&>b]:text-[15px] [&>b]:text-ink";
const TAB_ACTIVE: Partial<Record<TabId, string>> = {
  winner: "bg-white text-success shadow-sm [&>b]:text-success",
  loser: "bg-white text-danger shadow-sm [&>b]:text-danger",
};
const TAB_ACTIVE_DEFAULT = "bg-white text-primary shadow-sm [&>b]:text-primary";
export const tabClass = (tab: TabId, active: boolean): string => `${TAB} ${active ? TAB_ACTIVE[tab] ?? TAB_ACTIVE_DEFAULT : ""}`;

const LEAD_ROW = "min-w-0 cursor-pointer rounded-lg border border-transparent border-l-4 border-l-(--brand,var(--color-line)) px-2.5 py-[9px] hover:bg-soft";
const LEAD_ROW_SELECTED = "bg-[color-mix(in_srgb,var(--color-primary)_8%,white)] ring-1 ring-[color-mix(in_srgb,var(--color-primary)_35%,white)] ring-inset";
export const leadRowClass = (selected: boolean): string => `${LEAD_ROW} ${selected ? LEAD_ROW_SELECTED : ""}`;

export const SMALL = "mt-0.5 block wrap-anywhere text-mute";
export const QUICK_BUTTON = "border-[color-mix(in_srgb,var(--color-primary)_35%,white)] bg-[color-mix(in_srgb,var(--color-primary)_6%,white)] px-2.5 py-[5px] text-[13px] text-primary";
