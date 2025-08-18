// SPDX-License-Identifier: AGPL-3.0-or-later

import { http, listen, settings } from "../core/toolkit.ts";

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

const copyHashButton: HTMLElement | null = document.querySelector<HTMLElement>("#copy-hash");
if (copyHashButton) {
  listen("click", copyHashButton, async (event: Event) => {
    event.preventDefault();

    const { copiedText, hash } = copyHashButton.dataset;
    if (!(copiedText && hash)) return;

    try {
      await navigator.clipboard.writeText(hash);
      copyHashButton.innerText = copiedText;
    } catch (error) {
      console.error("Failed to copy hash:", error);
    }
  });
}
