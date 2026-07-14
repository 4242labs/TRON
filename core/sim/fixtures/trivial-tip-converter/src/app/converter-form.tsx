"use client";

import { useMemo, useState } from "react";
import { calculateTip, calculateTotal, splitAmount } from "@/lib/tip";
import {
  celsiusToFahrenheit,
  fahrenheitToCelsius,
  kmToMiles,
  milesToKm,
} from "@/lib/convert";

function toNumber(value: string): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

export default function ConverterForm() {
  const [bill, setBill] = useState("50");
  const [tipPercent, setTipPercent] = useState("20");
  const [people, setPeople] = useState("1");

  const [miles, setMiles] = useState("10");
  const [celsius, setCelsius] = useState("20");

  const billN = toNumber(bill);
  const tipPercentN = toNumber(tipPercent);
  const peopleN = Math.max(1, Math.trunc(toNumber(people)) || 1);

  const tip = useMemo(() => {
    try {
      return calculateTip(billN, tipPercentN);
    } catch {
      return 0;
    }
  }, [billN, tipPercentN]);

  const total = useMemo(() => {
    try {
      return calculateTotal(billN, tipPercentN);
    } catch {
      return 0;
    }
  }, [billN, tipPercentN]);

  const perPerson = useMemo(() => splitAmount(total, peopleN), [total, peopleN]);

  const milesN = toNumber(miles);
  const celsiusN = toNumber(celsius);

  return (
    <div className="w-full max-w-md space-y-10">
      <section aria-labelledby="tip-heading" className="space-y-4">
        <h2 id="tip-heading" className="text-lg font-medium">
          Tip calculator
        </h2>

        <label className="block text-sm">
          Bill amount
          <input
            type="number"
            min="0"
            step="0.01"
            value={bill}
            onChange={(e) => setBill(e.target.value)}
            className="mt-1 w-full rounded border border-foreground/20 bg-transparent px-3 py-2"
          />
        </label>

        <label className="block text-sm">
          Tip percent
          <input
            type="number"
            min="0"
            step="1"
            value={tipPercent}
            onChange={(e) => setTipPercent(e.target.value)}
            className="mt-1 w-full rounded border border-foreground/20 bg-transparent px-3 py-2"
          />
        </label>

        <label className="block text-sm">
          Split between
          <input
            type="number"
            min="1"
            step="1"
            value={people}
            onChange={(e) => setPeople(e.target.value)}
            className="mt-1 w-full rounded border border-foreground/20 bg-transparent px-3 py-2"
          />
        </label>

        <dl className="text-sm space-y-1">
          <div className="flex justify-between">
            <dt>Tip</dt>
            <dd data-testid="tip-amount">${tip.toFixed(2)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Total</dt>
            <dd data-testid="total-amount">${total.toFixed(2)}</dd>
          </div>
          <div className="flex justify-between font-medium">
            <dt>Per person</dt>
            <dd data-testid="per-person-amount">${perPerson.toFixed(2)}</dd>
          </div>
        </dl>
      </section>

      <section aria-labelledby="convert-heading" className="space-y-4">
        <h2 id="convert-heading" className="text-lg font-medium">
          Unit converter
        </h2>

        <label className="block text-sm">
          Miles
          <input
            type="number"
            step="0.01"
            value={miles}
            onChange={(e) => setMiles(e.target.value)}
            className="mt-1 w-full rounded border border-foreground/20 bg-transparent px-3 py-2"
          />
        </label>
        <p className="text-sm" data-testid="km-result">
          {milesN} miles = {milesToKm(milesN)} km ({kmToMiles(milesToKm(milesN))}{" "}
          miles back)
        </p>

        <label className="block text-sm">
          Celsius
          <input
            type="number"
            step="0.1"
            value={celsius}
            onChange={(e) => setCelsius(e.target.value)}
            className="mt-1 w-full rounded border border-foreground/20 bg-transparent px-3 py-2"
          />
        </label>
        <p className="text-sm" data-testid="fahrenheit-result">
          {celsiusN}&deg;C = {celsiusToFahrenheit(celsiusN)}&deg;F (
          {fahrenheitToCelsius(celsiusToFahrenheit(celsiusN))}&deg;C back)
        </p>
      </section>
    </div>
  );
}
