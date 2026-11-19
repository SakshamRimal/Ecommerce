import type { Money } from "./api/types";

/**
 * Parse a decimal string ("19.99" or "90") into integer cents without float drift.
 */
export function parseCents(amount: Money | number | null | undefined): number {
  if (amount === null || amount === undefined) return 0;
  const raw = String(amount).trim();
  if (!raw) return 0;

  const negative = raw.startsWith("-");
  const cleaned = raw.replace(/^[+-]/, "");
  const [wholePart = "0", fracPart = ""] = cleaned.split(".");
  const whole = Number.parseInt(wholePart || "0", 10);
  const paddedFrac = (fracPart + "00").slice(0, 2);
  const cents = Number.parseInt(paddedFrac, 10);

  if (Number.isNaN(whole) || Number.isNaN(cents)) return 0;
  const total = whole * 100 + cents;
  return negative ? -total : total;
}

export function centsToMoney(cents: number): Money {
  const negative = cents < 0;
  const abs = Math.abs(Math.round(cents));
  const whole = Math.floor(abs / 100);
  const rem = String(abs % 100).padStart(2, "0");
  return `${negative ? "-" : ""}${whole}.${rem}`;
}

export function multiplyMoney(unitPrice: Money, quantity: number): Money {
  return centsToMoney(parseCents(unitPrice) * quantity);
}

export function sumMoney(amounts: Money[]): Money {
  const totalCents = amounts.reduce((acc, a) => acc + parseCents(a), 0);
  return centsToMoney(totalCents);
}

export function formatMoney(
  amount: Money | number | null | undefined,
  currencyPrefix = "NRs",
  locale = "en-US",
): string {
  const cents = parseCents(amount);
  const formatted = new Intl.NumberFormat(locale, {
    style: "decimal",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(cents / 100);
  return `${currencyPrefix} ${formatted}`;
}

export function isValidMoneyInput(value: string): boolean {
  return /^\d+(\.\d{1,2})?$/.test(value.trim());
}

