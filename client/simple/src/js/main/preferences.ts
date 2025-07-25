import { searxng } from "./00_toolkit.ts";

const loadEngineDescriptions = async (): Promise<void> => {
  let engineDescriptions: Record<string, [string, string]> | null = null;
  try {
    const res = await searxng.http("GET", "engine_descriptions.json");
    engineDescriptions = await res.json();
  } catch (error) {
    console.error("Error fetching engineDescriptions:", error);
  }
  if (!engineDescriptions) return;

  for (const [engine_name, [description, source]] of Object.entries(engineDescriptions)) {
    const elements = document.querySelectorAll<HTMLElement>(`[data-engine-name="${engine_name}"] .engine-description`);
    const sourceText = ` (<i>${searxng.settings.translations?.Source}:&nbsp;${source}</i>)`;

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

searxng.ready(
  () => {
    const engineElements = document.querySelectorAll<HTMLElement>("[data-engine-name]");
    for (const engineElement of engineElements) {
      searxng.listen("mouseenter", engineElement, loadEngineDescriptions);
    }

    const engineToggles = document.querySelectorAll<HTMLInputElement>(
      "tbody input[type=checkbox][class~=checkbox-onoff]"
    );

    const enableAllEngines = document.querySelectorAll<HTMLElement>(".enable-all-engines");
    for (const engine of enableAllEngines) {
      searxng.listen("click", engine, () => toggleEngines(true, engineToggles));
    }

    const disableAllEngines = document.querySelectorAll<HTMLElement>(".disable-all-engines");
    for (const engine of disableAllEngines) {
      searxng.listen("click", engine, () => toggleEngines(false, engineToggles));
    }

    const copyHashButton = document.querySelector<HTMLElement>("#copy-hash");
    if (copyHashButton) {
      searxng.listen("click", copyHashButton, async (event: Event) => {
        event.preventDefault();

        const { copiedText, hash } = copyHashButton.dataset;
        if (!copiedText || !hash) return;

        try {
          await navigator.clipboard.writeText(hash);
          copyHashButton.innerText = copiedText;
        } catch (error) {
          console.error("Failed to copy hash:", error);
        }
      });
    }
  },
  { on: [searxng.endpoint === "preferences"] }
);
