import { describe, expect, it } from "vitest";
import {
  celsiusToFahrenheit,
  fahrenheitToCelsius,
  kmToMiles,
  milesToKm,
} from "./convert";

describe("distance conversion", () => {
  it("converts miles to kilometers", () => {
    expect(milesToKm(10)).toBe(16.09);
  });

  it("converts kilometers to miles", () => {
    expect(kmToMiles(16.0934)).toBe(10);
  });
});

describe("temperature conversion", () => {
  it("converts Fahrenheit to Celsius", () => {
    expect(fahrenheitToCelsius(212)).toBe(100);
  });

  it("converts Celsius to Fahrenheit", () => {
    expect(celsiusToFahrenheit(0)).toBe(32);
  });
});
