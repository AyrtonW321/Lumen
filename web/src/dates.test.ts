import { describe, expect, it } from "vitest";
import { quickDate } from "./dates";

const wed = new Date(2026, 9, 21); // Wed Oct 21, 2026

describe("quickDate", () => {
  it("adds short offsets", () => {
    expect(quickDate("1d", wed)).toBe("2026-10-22");
    expect(quickDate("1w", wed)).toBe("2026-10-28");
  });

  it("moves a weekend result to Monday", () => {
    expect(quickDate("2d", wed)).toBe("2026-10-23");
    expect(quickDate("2d", new Date(2026, 9, 22))).toBe("2026-10-26"); // Sat Oct 24
  });

  it("clamps month-end and lands Jan 1 on a weekday", () => {
    expect(quickDate("1m", new Date(2026, 0, 31))).toBe("2026-03-02"); // Feb 28 is a Sat
    expect(quickDate("jan1", wed)).toBe("2027-01-01");
  });
});
