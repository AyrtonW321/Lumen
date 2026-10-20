// Pure date helpers for the reschedule quick buttons. No DOM, so they run under vitest.
import type { QuickKind } from "./constants";

export function isoLocal(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// Moves d by n months in place, clamping to the end of a shorter month (Jan 31 + 1 month = Feb 28).
function addMonths(d: Date, n: number): void {
  const day = d.getDate(); d.setDate(1); d.setMonth(d.getMonth() + n);
  d.setDate(Math.min(day, new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate()));
}

// A result on a weekend moves to the following Monday.
export function quickDate(kind: QuickKind, today = new Date()): string {
  const d = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  if (kind === "1d") d.setDate(d.getDate() + 1);
  else if (kind === "2d") d.setDate(d.getDate() + 2);
  else if (kind === "1w") d.setDate(d.getDate() + 7);
  else if (kind === "1m") addMonths(d, 1);
  else if (kind === "jan1") d.setFullYear(d.getFullYear() + 1, 0, 1);
  else if (kind === "1y") addMonths(d, 12);
  else if (kind === "2y") addMonths(d, 24);
  if (d.getDay() === 6) d.setDate(d.getDate() + 2);
  if (d.getDay() === 0) d.setDate(d.getDate() + 1);
  return isoLocal(d);
}
