/**
 * tip.ts — pure tip-calculator domain logic. No React, no I/O: safe to unit
 * test directly and safe to import from any client or server component.
 */

function round2(n: number): number {
  return Math.round((n + Number.EPSILON) * 100) / 100;
}

/** The tip amount owed on `bill` at `tipPercent` (e.g. 20 for 20%). */
export function calculateTip(bill: number, tipPercent: number): number {
  if (bill < 0) throw new Error("bill must be non-negative");
  if (tipPercent < 0) throw new Error("tipPercent must be non-negative");
  return round2(bill * (tipPercent / 100));
}

/** Bill + tip, rounded to the cent. */
export function calculateTotal(bill: number, tipPercent: number): number {
  return round2(bill + calculateTip(bill, tipPercent));
}

/** Split `total` evenly across `people` (>= 1), rounded to the cent. */
export function splitAmount(total: number, people: number): number {
  if (people <= 0) throw new Error("people must be a positive integer");
  return round2(total / people);
}
