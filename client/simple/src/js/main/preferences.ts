// SPDX-License-Identifier: AGPL-3.0-or-later

import { http, listen, settings } from "../toolkit.ts";
import { assertElement } from "../util/assertElement.ts";

let engineDescriptions: Record<string, [string, string]> | undefined;

const loadEngineDescriptions = async (): Promise<void> => {
  if (engineDescriptions) return;
  try {
    const res = await http("GET", "engine_descriptions.json");
    engineDescriptions = await res.json();
  } catch (error) {
    console.error("Error fetching engineDescriptions:", error);
  }
  if (!engineDescriptions) return;

  for (const [engine_name, [description, source]] of Object.entries(engineDescriptions)) {
    const elements = document.querySelectorAll<HTMLElement>(`[data-engine-name="${engine_name}"] .engine-description`);
    const sourceText = ` (<i>${settings.translations?.Source}:&nbsp;${source}</i>)`;

    for (const element of elements) {
      element.innerHTML = description + sourceText;
    }
  }
};

const toggleEngines = (enable: boolean, engineToggles: NodeListOf<HTMLInputElement>): void => {
  for (const engineToggle of engineToggles) {
    // check if element visible, so that only engines of the current category are modified
    if (engineToggle.offsetParent) {
      engineToggle.checked = !enable;
    }
  }
};

const engineElements: NodeListOf<HTMLElement> = document.querySelectorAll<HTMLElement>("[data-engine-name]");
for (const engineElement of engineElements) {
  listen("mouseenter", engineElement, loadEngineDescriptions);
}

const engineToggles: NodeListOf<HTMLInputElement> = document.querySelectorAll<HTMLInputElement>(
  "tbody input[type=checkbox][class~=checkbox-onoff]"
);

const enableAllEngines: NodeListOf<HTMLElement> = document.querySelectorAll<HTMLElement>(".enable-all-engines");
for (const engine of enableAllEngines) {
  listen("click", engine, () => toggleEngines(true, engineToggles));
}

const disableAllEngines: NodeListOf<HTMLElement> = document.querySelectorAll<HTMLElement>(".disable-all-engines");
for (const engine of disableAllEngines) {
  listen("click", engine, () => toggleEngines(false, engineToggles));
}

listen("click", "#copy-hash", async function (this: HTMLElement) {
  const target = this.parentElement?.querySelector<HTMLPreElement>("pre");
  assertElement(target);

  if (window.isSecureContext) {
    await navigator.clipboard.writeText(target.innerText);
  } else {
    const selection = window.getSelection();
    if (selection) {
      const range = document.createRange();
      range.selectNodeContents(target);
      selection.removeAllRanges();
      selection.addRange(range);
      document.execCommand("copy");
    }
  }

  const copiedText = this.dataset.copiedText;
  if (copiedText) {
    this.innerText = copiedText;
  }
});
