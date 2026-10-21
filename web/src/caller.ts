import { config } from "./state";
import { $, store, toast } from "./util";

export function bindCaller(): void {
  const input = $<HTMLInputElement>("caller");
  const saved = config().caller_name;
  input.value = saved ?? store("lumen.caller") ?? "";
  let revision = Date.now(), errorShown = false;
  const persist = () => {
    // Local backup is immediate; keepalive lets the write finish if the window closes.
    store("lumen.caller", input.value);
    revision = Math.max(Date.now(), revision + 1);
    void fetch("/api/settings/caller", {
      method: "POST", headers: {"Content-Type":"application/json"}, keepalive: true,
      body: JSON.stringify({name:input.value, revision}),
    }).then(response => {
      if (!response.ok) throw new Error("Could not save name");
      errorShown = false;
    }).catch(() => {
      if (!errorShown) toast("Name saved in this browser. Reconnect to Lumen to save it across sessions.");
      errorShown = true;
    });
  };
  input.addEventListener("input", persist);
  input.addEventListener("change", persist);
  window.addEventListener("pagehide", persist);
  // Migrate a name previously stored only in this browser's local storage.
  if (saved == null && input.value) persist();
  else store("lumen.caller", input.value);
}
