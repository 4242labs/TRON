import { describe, expect, it } from "vitest";
import { calculateTip, calculateTotal, splitAmount } from "./tip";

describe("calculateTip", () => {
  it("computes the tip amount for a typical bill", () => {
    expect(calculateTip(50, 20)).toBe(10);
  });

  it("returns 0 for a 0% tip", () => {
    expect(calculateTip(50, 0)).toBe(0);
  });

  it("rejects a negative bill", () => {
    expect(() => calculateTip(-1, 20)).toThrow();
  });
});

describe("calculateTotal", () => {
  it("sums the bill and the computed tip", () => {
    expect(calculateTotal(50, 20)).toBe(60);
  });
});

describe("splitAmount", () => {
  it("divides the total evenly across the party size", () => {
    expect(splitAmount(60, 3)).toBe(20);
  });
});
