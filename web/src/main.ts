
import "./styles.css";
import "./workspace.css";
import { setupShell } from "./shell";
import { refresh } from "./actions";
import { TABS } from "./constants";
import { bindEvents } from "./events";
import { showModel } from "./render";
import { state } from "./state";
import type { Config } from "./types";
import { $, api, options, store } from "./util";

function fillSelects(cfg: Config): void {
  const brands = Object.entries(cfg.brands).map(([b, r]) => [b, `${b} (${r})`] as const);
  const lists = Object.entries(cfg.sources);
  options($("fBrand"), brands, "All companies"); options($("nBrand"), brands); options($("lBrand"), brands);
  $("fProduct").innerHTML = cfg.products.map(p => `<label><input type="checkbox" value="${p}"> ${p}</label>`).join("");
  options($("nSource"), lists.slice(0, 2)); options($("lSource"), lists);
  options($("cType"), Object.keys(cfg.phone_types).map(t => [t, t.charAt(0).toUpperCase() + t.slice(1)] as const), "Phone type");
  options($("dMeeting"), cfg.meeting_types.map(m => [m, m] as const), "Meeting type");
  $("nProducts").innerHTML = cfg.products.map(p => `<label><input type="checkbox" name="product" value="${p}"> ${p}</label>`).join("");
}

async function start(): Promise<void> {
  const cfg = await api<Config>("/api/config");
  state.cfg = cfg;
  fillSelects(cfg);
  const saved = store("lumen.tab"); const tab = TABS.find(([t]) => t === saved); if (tab) state.tab = tab[0];
  setupShell();
  bindEvents();
  showModel(cfg.model);
  await refresh();
}

void start();
