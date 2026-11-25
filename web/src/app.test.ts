// @vitest-environment jsdom
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, it, vi } from "vitest";
import type { Config, LeadDetail, LeadRow } from "./types";

const config: Config = {
  brands: { Haneco: "Canada", JWL: "Chicago", Exceledy: "Texas" },
  products: ["Solar", "Lighting", "BESS", "EV Charging"],
  sources: { new: "Leads", "follow-up": "Follow-ups", winner: "Winners", loser: "Losers" },
  outcomes: {
    VM: { label: "Voicemail / no answer", key: "v", retry: 2 },
    WIN: {label:"Winner",key:"",retry:null,closes:true,move_to:"winner"},
    LOST: {label:"Loser",key:"",retry:null,closes:true,move_to:"loser"},
    CALLBACK: {label:"Callback scheduled",key:"",retry:1,move_to:"follow-up"},
  },
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
  lighting_reference: null, meeting_type: null, appt_at: null, traits: [], badges: [],
  contacts: [{ id: 5, lead_id: 1, name: "Amy Test", title: "Owner", phone: null, email: null, ext: null, phone_type: null, prefers_email: 0, created_at: "2026-10-19T09:00:00" }],
  activities: [],
};

it("loads leads, shows one, and selects it on click", async () => {
  const callbackRows = [
    { id: 1, name: "Test Co", brand: "Haneco", section: "today", callback_at: "2026-10-21T14:00", late: true,
      contact: { name: "Amy Test", title: "Owner" }, phone: "555-010-0199", ext: "12", last_note: "Call after lunch",
      traits: [{ name: "Nice", note: null, person: true }], badges: [] },
    { id: 2, name: "Later Co", brand: "JWL", section: "upcoming", callback_at: "2026-10-25", late: false,
      contact: null, phone: null, ext: null, last_note: null, traits: [], badges: [] },
  ];
  const routes: Record<string, unknown> = { "/api/config": {...config, warning_traits: ["Has concerns", "Rude"]}, "/api/leads": [row], "/api/leads/1": detail,
    "/api/traits": { person: ["Nice", "Rude"], company: ["Budget-tight"] }, "/api/callbacks": callbackRows };
  const fetchMock = vi.fn(async (path: string, init?: RequestInit) => {
    if (path === "/api/leads/1" && init?.body) {
      const body = JSON.parse(String(init.body));
      if (body.brand) { detail.brand = body.brand; row.brand = detail.brand; }
      if (body.products) { detail.products = body.products.join(","); row.products = detail.products; }
    }
    if (path === "/api/activities" && init?.body) {
      const body = JSON.parse(String(init.body));
      detail.activities.unshift({...body,id:detail.activities.length + 1,timestamp:"2026-10-21T09:00:00",weekday:"Wed",hour_block:"9-11",myphoner_comment:"Saved call"});
      detail.source = body.outcome === "WIN" ? "winner" : body.outcome === "LOST" ? "loser" : "follow-up";
      detail.closed = body.outcome === "CALLBACK" ? null : body.outcome;
      row.source = detail.source;
      return {ok:true,json:async () => ({myphoner_comment:"Saved call"})};
    }
    return { ok: true, json: async () => routes[path] };
  });
  vi.stubGlobal("fetch", fetchMock);
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
  expect((document.querySelector('[name="contact_name"]') as HTMLInputElement).value).toBe("Amy Test");
  document.getElementById("collapseSidebar")!.click();
  expect(document.getElementById("sidebar")!.classList.contains("collapsed")).toBe(true);
  expect(document.getElementById("collapseSidebar")!.getAttribute("aria-expanded")).toBe("false");
  const { state } = await import("./state");
  const { renderPanel, renderList } = await import("./render");
  state.tab = "all";
  state.leads = [row, {...row,id:2,name:"Lighting winner",products:"Lighting",source:"winner"}, {...row,id:3,name:"Battery loser",products:"BESS",source:"loser"}];
  const products = document.querySelectorAll<HTMLInputElement>("#fProduct input");
  products[0]!.checked = true; products[1]!.checked = true;
  products[0]!.dispatchEvent(new Event("input",{bubbles:true}));
  expect(document.querySelectorAll("#list [data-id]")).toHaveLength(2);
  const status = document.getElementById("fStatus") as HTMLSelectElement;
  status.value = "winner"; status.dispatchEvent(new Event("input",{bubbles:true}));
  expect(document.querySelectorAll("#list [data-id]")).toHaveLength(1);
  expect(document.getElementById("list")!.textContent).toContain("Lighting winner");
  document.getElementById("resetFilters")!.click();
  expect(document.querySelectorAll("#list [data-id]")).toHaveLength(3);
  state.detail!.activities = [{id:1,lead_id:1,contact_id:5,timestamp:"2026-10-20T09:00:00",weekday:"Tue",hour_block:"9-11",outcome:"VM",note:"First line\nSecond line",caller:null,myphoner_comment:""}];
  renderPanel();
  expect(document.querySelector(".history-note")!.textContent).toBe("First line\nSecond line");
  state.leads = [{...row, products:"Solar,Lighting,BESS", source:"follow-up"}];
  renderList();
  const lead = document.querySelector("#list [data-id]")!;
  expect(lead.querySelector(".lead-heading > .status")!.textContent).toBe("Follow-ups");
  expect(lead.querySelector(".more-products")!.textContent).toBe("+1");
  expect(lead.querySelector(".more-products")!.getAttribute("aria-label")).toContain("BESS");
  expect(lead.querySelectorAll(".lead-tags .chip")).toHaveLength(4);
  state.leads[0]!.products = "Solar,Lighting";
  renderList();
  expect(document.querySelector(".more-products")).toBeNull();
  const themeToggle = document.getElementById("themeToggle")!;
  const initialTheme = document.documentElement.dataset.theme;
  themeToggle.click();
  expect(document.documentElement.dataset.theme).toBe(initialTheme === "dark" ? "light" : "dark");
  expect(localStorage.getItem("lumen.theme")).toBe(document.documentElement.dataset.theme);
  expect(themeToggle.getAttribute("aria-label")).toBe(initialTheme === "dark" ? "Switch to dark mode" : "Switch to light mode");
  themeToggle.click();
  expect(document.documentElement.dataset.theme).toBe(initialTheme);
  const contactBeforeEdit = state.form.contact_id;
  (document.querySelector('#list [data-company-lead="1"]') as HTMLButtonElement).click();
  const editor = document.querySelector<HTMLElement>(".company-editor")!;
  expect(editor.hidden).toBe(false);
  (editor.querySelector("select") as HTMLSelectElement).value = "JWL";
  editor.querySelector("form")!.dispatchEvent(new Event("submit", {bubbles:true,cancelable:true}));
  await vi.waitFor(() => expect(editor.hidden).toBe(true));
  expect(fetchMock).toHaveBeenCalledWith("/api/leads/1", expect.objectContaining({method:"POST",body:JSON.stringify({brand:"JWL"})}));
  expect(document.querySelector("#lCompanyTag button")!.textContent).toBe("JWL");
  expect(state.form.contact_id).toBe(contactBeforeEdit);
  (document.querySelector("#lCompanyTag button") as HTMLButtonElement).click();
  expect(editor.hidden).toBe(false);
  editor.querySelector("select")!.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}));
  expect(editor.hidden).toBe(true);
  const callsBeforeClassification = fetchMock.mock.calls.length;
  document.getElementById("winner")!.click();
  expect(fetchMock.mock.calls).toHaveLength(callsBeforeClassification);
  expect(document.getElementById("outcomeField")!.hidden).toBe(true);
  expect(document.getElementById("winner")!.getAttribute("aria-pressed")).toBe("true");
  (document.getElementById("note") as HTMLTextAreaElement).value = "Owner accepted.\nReady to proceed.";
  document.getElementById("save")!.click();
  await vi.waitFor(() => expect(document.getElementById("history")!.textContent).toContain("Owner accepted."));
  expect(document.getElementById("history")!.textContent).toContain("Winner");
  document.getElementById("callback")!.click();
  expect(document.getElementById("outcomeField")!.hidden).toBe(true);
  (document.getElementById("callback_date") as HTMLInputElement).value = "2026-10-23";
  (document.getElementById("note") as HTMLTextAreaElement).value = "Follow up next week";
  document.getElementById("save")!.click();
  await vi.waitFor(() => expect(document.getElementById("history")!.textContent).toContain("Follow up next week"));
  expect(document.getElementById("history")!.textContent).toContain("Winner");
  expect(state.detail!.source).toBe("follow-up");
  expect(state.detail!.closed).toBeNull();
  expect(document.querySelectorAll("#lProducts > .chip")).toHaveLength(1);
  const picker = document.querySelector<HTMLDetailsElement>(".product-picker")!;
  picker.open = true;
  document.querySelector<HTMLInputElement>('[data-product="EV Charging"]')!.click();
  await vi.waitFor(() => expect(document.querySelectorAll("#lProducts > .chip")).toHaveLength(2));
  expect(document.querySelector("#lProducts")!.textContent).toContain("EV Charging");
  expect(document.querySelector<HTMLDetailsElement>(".product-picker")!.open).toBe(true);
  expect(document.querySelectorAll("#lProducts > .chip")).toHaveLength(2);
  document.querySelector<HTMLInputElement>('[data-product="EV Charging"]')!.click();
  await vi.waitFor(() => expect(document.querySelectorAll("#lProducts > .chip")).toHaveLength(1));
  expect(document.querySelectorAll("#lProducts > .chip")).toHaveLength(1);

  // Callbacks dropdown: badge counts urgent rows only, search finds phone digits, click opens the lead.
  expect(document.getElementById("callbacksBadge")!.textContent).toBe("1");
  document.getElementById("callbacksBtn")!.click();
  expect(document.getElementById("callbacksPanel")!.hidden).toBe(false);
  await vi.waitFor(() => expect(document.querySelectorAll("#callbacksList [data-callback]")).toHaveLength(2));
  expect(document.querySelector(".callback-today")!.textContent).toContain("ext 12");
  expect(document.querySelector(".callback-late")).not.toBeNull();
  const cbSearch = document.getElementById("callbacksSearch") as HTMLInputElement;
  cbSearch.value = "0100199"; cbSearch.dispatchEvent(new Event("input", { bubbles: true }));
  expect(document.querySelectorAll("#callbacksList [data-callback]")).toHaveLength(1);
  (document.querySelector("#callbacksList [data-callback]") as HTMLElement).click();
  expect(document.getElementById("callbacksPanel")!.hidden).toBe(true);

  // Trait filter: once = must have, twice = must not have; search also reads trait notes.
  state.tab = "all";
  state.leads = [{ ...row, traits: [{ name: "Nice", note: "loves hockey", person: true }], main_contact: { id: 5, name: "Amy Test", title: "Owner", pinned: false } },
                 { ...row, id: 2, name: "Plain Co", traits: [] }];
  renderList();
  expect(document.querySelector("#list .trait-chip")!.textContent).toBe("Nice");
  expect(document.querySelector("#list .lead-contact")!.textContent).toBe("Amy Test · Owner");
  const nice = () => document.querySelector<HTMLElement>('[data-trait-filter="person:Nice"]')!;
  nice().click();
  expect(document.getElementById("list")!.textContent).not.toContain("Plain Co");
  nice().click();
  expect(document.querySelectorAll("#list [data-id]")).toHaveLength(1);
  expect(document.getElementById("list")!.textContent).toContain("Plain Co");
  nice().click();
  const search = document.getElementById("search") as HTMLInputElement;
  search.value = "hockey"; search.dispatchEvent(new Event("input", { bubbles: true }));
  expect(document.querySelectorAll("#list [data-id]")).toHaveLength(1);
  search.value = ""; search.dispatchEvent(new Event("input", { bubbles: true }));

  // Pin button posts the contact as main contact.
  (document.querySelector('#contacts [data-main="5"]') as HTMLElement).click();
  await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/leads/1", expect.objectContaining({ body: JSON.stringify({ main_contact_id: 5 }) })));

  // Callback outcome shows the "expecting their call" checkbox.
  document.getElementById("callback")!.click();
  expect(document.getElementById("expectingField")!.hidden).toBe(false);
  document.getElementById("regularCall")!.click();
  expect(document.getElementById("expectingField")!.hidden).toBe(true);
  expect(document.querySelector("#headsUp [data-trait-add]")).not.toBeNull();

  // Trait picker: preset fills the name, a known name disables "save for reuse", submit posts the trait.
  (document.querySelector('#contacts [data-trait-add="5"]') as HTMLElement).click();
  const traitEditor = document.getElementById("traitEditor")!;
  expect(traitEditor.hidden).toBe(false);
  (traitEditor.querySelector('[data-trait-pick="Rude"]') as HTMLElement).click();
  expect((traitEditor.querySelector("[name=name]") as HTMLInputElement).value).toBe("Rude");
  expect((traitEditor.querySelector("[name=save]") as HTMLInputElement).disabled).toBe(true);
  (traitEditor.querySelector("[name=note]") as HTMLInputElement).value = "Short on the phone";
  traitEditor.querySelector("form")!.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(traitEditor.hidden).toBe(true));
  expect(fetchMock).toHaveBeenCalledWith("/api/traits", expect.objectContaining({
    body: JSON.stringify({ lead_id: 1, contact_id: 5, name: "Rude", note: "Short on the phone", save: false }) }));
});

function loadPage(): void {
  const html = readFileSync(resolve(__dirname, "../index.html"), "utf8");
  document.body.innerHTML = /<body[^>]*>([\s\S]*)<\/body>/.exec(html)![1]!.replace(/<script[\s\S]*?<\/script>/, "");
}

it("shows list skeletons at start and Retry when leads cannot load", async () => {
  vi.resetModules();
  loadPage();
  expect(document.querySelectorAll("#list .skel")).toHaveLength(8);
  vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
  await import("./main");
  await vi.waitFor(() => expect(document.querySelector("#list .load-error")).not.toBeNull());
  expect(document.querySelectorAll("#list .skel")).toHaveLength(0);
  expect(document.getElementById("list")!.textContent).toContain("Is Lumen running?");
  expect(document.querySelector("#list .load-error button")!.textContent).toBe("Retry");
});

it("shows a panel skeleton for a slow lead, then Retry when it fails", async () => {
  vi.resetModules();
  loadPage();
  let fail!: (e: Error) => void;
  const routes: Record<string, unknown> = { "/api/config": config, "/api/leads": [{ ...row, source: "new" }],
    "/api/traits": { person: [], company: [] }, "/api/callbacks": [] };
  vi.stubGlobal("fetch", vi.fn(async (path: string) => path === "/api/leads/1"
    ? new Promise((_, reject) => { fail = reject; })
    : { ok: true, json: async () => routes[path] }));
  await import("./main");
  await vi.waitFor(() => expect(document.querySelectorAll("#list [data-id]")).toHaveLength(1));
  expect(document.getElementById("list")!.hasAttribute("aria-busy")).toBe(false);
  (document.querySelector("#list [data-id]") as HTMLElement).click();
  expect(document.getElementById("panelLoad")!.hidden).toBe(true);
  await vi.waitFor(() => expect(document.querySelectorAll("#panelLoad .skel").length).toBeGreaterThan(0));
  expect(document.getElementById("empty")!.hidden).toBe(true);
  fail(new TypeError("Failed to fetch"));
  await vi.waitFor(() => expect(document.querySelector("#panelLoad .load-error button")).not.toBeNull());
  expect(document.getElementById("panel")!.hidden).toBe(true);
});
