import type { Brand, Product, TabId } from "./types";

// Full class names, written out so Tailwind can find them.
export const BRAND_VAR: Record<Brand, string> = { Haneco: "--color-haneco", JWL: "--color-jwl", Exceledy: "--color-exceledy" };
export const PRODUCT_VAR: Record<Product, string> = { Solar: "--color-solar", Lighting: "--color-lighting", BESS: "--color-bess", "EV Charging": "--color-ev" };

export const TABS: ReadonlyArray<readonly [TabId, string]> = [
  ["new", "Leads"], ["follow-up", "Follow-ups"], ["winner", "Winners"], ["loser", "Losers"], ["all", "All"],
];

export const QUICK = [
  ["1d", "+1 day"], ["2d", "+2 days"], ["1w", "+1 week"], ["1m", "+1 month"],
  ["jan1", "Jan 1 next year"], ["1y", "+1 year"], ["2y", "+2 years"],
] as const;

export type QuickKind = (typeof QUICK)[number][0];
