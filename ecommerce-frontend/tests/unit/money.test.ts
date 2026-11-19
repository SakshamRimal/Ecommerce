import { describe, expect, it } from "vitest";
import {
  centsToMoney,
  formatMoney,
  isValidMoneyInput,
  multiplyMoney,
  parseCents,
  sumMoney,
} from "../../src/lib/money";

describe("money utilities (integer-cents decimal string arithmetic)", () => {
  it("parses exact decimal strings into integer cents without float drift", () => {
    expect(parseCents("19.99")).toBe(1999);
    expect(parseCents("0.10")).toBe(10);
    expect(parseCents("0.20")).toBe(20);
    expect(parseCents("249")).toBe(24900);
    expect(parseCents("1299.5")).toBe(129950);
  });

  it("converts cents back to canonical two-decimal Money string", () => {
    expect(centsToMoney(1999)).toBe("19.99");
    expect(centsToMoney(30)).toBe("0.30");
    expect(centsToMoney(0)).toBe("0.00");
  });

  it("avoids classic IEEE-754 0.1 + 0.2 !== 0.3 bug in sumMoney and multiplyMoney", () => {
    expect(sumMoney(["0.10", "0.20"])).toBe("0.30");
    expect(multiplyMoney("19.99", 3)).toBe("59.97");
  });

  it("formats money for display using Intl.NumberFormat", () => {
    expect(formatMoney("249.00")).toBe("$249.00");
    expect(formatMoney("19.99")).toBe("$19.99");
  });

  it("validates user money input strings", () => {
    expect(isValidMoneyInput("49.99")).toBe(true);
    expect(isValidMoneyInput("100")).toBe(true);
    expect(isValidMoneyInput("12.345")).toBe(false);
    expect(isValidMoneyInput("-5.00")).toBe(false);
    expect(isValidMoneyInput("abc")).toBe(false);
  });
});

