// @vitest-environment jsdom
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it, vi } from "vitest";
import type { Config, LeadDetail, LeadRow } from "./types";

const config: Config = {
  brands: { Haneco: "Canada", JWL: "Chicago", Exceledy: "Texas" },
  products: ["Solar", "Lighting", "BESS"],
  sources: { new: "Leads", "follow-up": "Follow-ups", winner: "Winners", loser: "Losers" },
  outcomes: { VM: { label: "Voicemail / no answer", key: "v", retry: 2 } },
  phone_types: { direct: "D", mobile: "M", business: "B" },
  meeting_types: ["In-person", "Online", "Phone"],
  model: null,
};
const row: LeadRow = {
  id: 1, name: "Test Co", brand: "Haneco", products: "Solar", source: "new", list_name: null, label: null, closed: null,
  next_action_date: null, last_outcome: null, attempts: 0, advice: ["New lead: make the first call"], tier: 3, open: true, due: true,
};
const detail: LeadDetail = {
  ...row, phone: null, created_at: "2026-10-19T09:00:00", address: null, facility_size: null, solar_reference: null,
  lighting_reference: null, meeting_type: null, appt_at: null,
  contacts: [{ id: 5, lead_id: 1, name: "Amy Test", title: "Owner", phone: null, email: null, ext: null, phone_type: null, prefers_email: 0, created_at: "2026-10-19T09:00:00" }],
  activities: [],
};

it("loads leads, shows one, and selects it on click", async () => {
  const routes: Record<string, unknown> = { "/api/config": config, "/api/leads": [row], "/api/leads/1": detail };
  vi.stubGlobal("fetch", async (path: string) => ({ ok: true, json: async () => routes[path] }));
  const html = readFileSync(resolve(__dirname, "../index.html"), "utf8");
  document.body.innerHTML = /<body[^>]*>([\s\S]*)<\/body>/.exec(html)![1]!.replace(/<script[\s\S]*?<\/script>/, "");

  await import("./main");
  await vi.waitFor(() => expect(document.querySelectorAll("#list [data-id]")).toHaveLength(1));
  expect(document.getElementById("list")!.textContent).toContain("Test Co");
  expect(document.querySelector("#tabs [data-tab=new] b")!.textContent).toBe("1");

  (document.querySelector("#list [data-id]") as HTMLElement).click();
  await vi.waitFor(() => expect(document.getElementById("panel")!.hidden).toBe(false));
  expect(document.getElementById("lName")!.textContent).toBe("Test Co");
  expect(document.getElementById("contacts")!.textContent).toContain("Amy Test");
  expect(document.getElementById("lAdvice")!.textContent).toContain("first call");
});
