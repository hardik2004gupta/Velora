import { describe, it, expect } from "vitest";
import { formatCost, formatLatency, formatTokens, truncate } from "@/lib/utils";

describe("formatCost", () => {
  it("formats sub-cent amounts in milli-cents", () => {
    expect(formatCost(0.0001)).toBe("$0.1000m");
  });
  it("formats amounts under $1", () => {
    expect(formatCost(0.05)).toBe("$0.0500");
  });
  it("formats amounts over $1", () => {
    expect(formatCost(2.5)).toBe("$2.50");
  });
});

describe("formatLatency", () => {
  it("shows ms for sub-second values", () => {
    expect(formatLatency(820)).toBe("820ms");
  });
  it("shows seconds for values >= 1000ms", () => {
    expect(formatLatency(1500)).toBe("1.50s");
  });
});

describe("formatTokens", () => {
  it("formats millions", () => {
    expect(formatTokens(1_500_000)).toBe("1.5M");
  });
  it("formats thousands", () => {
    expect(formatTokens(4200)).toBe("4.2K");
  });
  it("returns raw for small values", () => {
    expect(formatTokens(42)).toBe("42");
  });
});

describe("truncate", () => {
  it("truncates long strings", () => {
    expect(truncate("hello world", 5)).toBe("hello…");
  });
  it("leaves short strings intact", () => {
    expect(truncate("hi", 10)).toBe("hi");
  });
});
