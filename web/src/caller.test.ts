// @vitest-environment jsdom
import { beforeEach, expect, it, vi } from "vitest";
const settings = vi.hoisted(() => ({caller_name: null as string | null}));
vi.mock("./state", () => ({config: () => settings}));
import { bindCaller } from "./caller";

beforeEach(() => {
  document.body.innerHTML = '<input id="caller"><div id="toast"></div>';
  localStorage.clear();
  settings.caller_name = null;
  vi.stubGlobal("fetch", vi.fn(async () => ({ok:true})));
});

it("restores the database name in a fresh browser session and saves while typing", async () => {
  settings.caller_name = "Alex Morgan";
  bindCaller();
  const input = document.getElementById("caller") as HTMLInputElement;
  expect(input.value).toBe("Alex Morgan");
  input.value = "Alex";
  input.dispatchEvent(new Event("input"));
  expect(localStorage.getItem("lumen.caller")).toBe("Alex");
  expect(fetch).toHaveBeenCalledWith("/api/settings/caller", expect.objectContaining({
    method:"POST", keepalive:true, body:expect.stringContaining('"name":"Alex"'),
  }));
});

it("migrates an existing browser name but respects an intentionally cleared name", () => {
  localStorage.setItem("lumen.caller", "Legacy name");
  bindCaller();
  expect(fetch).toHaveBeenCalledTimes(1);
  settings.caller_name = "";
  bindCaller();
  expect((document.getElementById("caller") as HTMLInputElement).value).toBe("");
});
