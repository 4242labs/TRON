/**
 * convert.ts — pure unit-conversion domain logic (distance + temperature).
 * No React, no I/O: safe to unit test directly and safe to import from any
 * client or server component.
 */

function round2(n: number): number {
  return Math.round((n + Number.EPSILON) * 100) / 100;
}

const KM_PER_MILE = 1.60934;

export function milesToKm(miles: number): number {
  return round2(miles * KM_PER_MILE);
}

export function kmToMiles(km: number): number {
  return round2(km / KM_PER_MILE);
}

export function fahrenheitToCelsius(f: number): number {
  return round2(((f - 32) * 5) / 9);
}

export function celsiusToFahrenheit(c: number): number {
  return round2((c * 9) / 5 + 32);
}
