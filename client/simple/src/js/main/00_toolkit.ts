import type { KeyBindingLayout } from "./keyboard.ts";

type Settings = {
  theme_static_path?: string;
  method?: string;
  hotkeys?: KeyBindingLayout;
  infinite_scroll?: boolean;
  autocomplete?: boolean;
  autocomplete_min?: number;
  search_on_category_select?: boolean;
  translations?: Record<string, string>;
  [key: string]: unknown;
};

type ReadyOptions = {
  // all values must be truthy for the callback to be executed
  on?: (boolean | undefined)[];
};

const getEndpoint = (): string => {
  const endpointClass = Array.from(document.body.classList).find((className) => className.endsWith("_endpoint"));
  return endpointClass?.split("_")[0] ?? "";
};

const getSettings = (): Settings => {
  const settings = document.querySelector("script[client_settings]")?.getAttribute("client_settings");
  if (!settings) return {};

  try {
    return JSON.parse(atob(settings));
  } catch (error) {
    console.error("Failed to load client_settings:", error);
    return {};
  }
};

type AssertElement = (element?: Element | null) => asserts element is Element;
export const assertElement: AssertElement = (element?: Element | null): asserts element is Element => {
  if (!element) {
    throw new Error("Bad assertion: DOM element not found");
  }
};

export const searxng = {
  // dynamic functions
  closeDetail: undefined as (() => void) | undefined,
  scrollPageToSelected: undefined as (() => void) | undefined,
  selectImage: undefined as ((resultElement: Element) => void) | undefined,
  selectNext: undefined as ((openDetailView?: boolean) => void) | undefined,
  selectPrevious: undefined as ((openDetailView?: boolean) => void) | undefined,

  endpoint: getEndpoint(),

  http: async (method: string, url: string | URL, data?: BodyInit): Promise<Response> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    const res = await fetch(url, {
      body: data,
      method,
      signal: controller.signal
    }).finally(() => clearTimeout(timeoutId));
    if (!res.ok) {
      throw new Error(res.statusText);
    }

    return res;
  },

  listen: <K extends keyof DocumentEventMap, E extends Element>(
    type: string | K,
    target: string | Document | E,
    listener: (this: E, event: DocumentEventMap[K]) => void,
    options?: AddEventListenerOptions
  ): void => {
    if (typeof target !== "string") {
      target.addEventListener(type, listener as EventListener, options);
      return;
    }

    document.addEventListener(
      type,
      (event: Event) => {
        for (const node of event.composedPath()) {
          if (node instanceof Element && node.matches(target)) {
            try {
              listener.call(node as E, event as DocumentEventMap[K]);
            } catch (error) {
              console.error(error);
            }
            break;
          }
        }
      },
      options
    );
  },

  ready: (callback: () => void, options?: ReadyOptions): void => {
    for (const condition of options?.on ?? []) {
      if (!condition) {
        return;
      }
    }

    if (document.readyState !== "loading") {
      callback();
    } else {
      searxng.listen("DOMContentLoaded", document, callback, { once: true });
    }
  },

  settings: getSettings()
};

searxng.listen("click", ".close", function (this: Element) {
  (this.parentNode as Element)?.classList.add("invisible");
});
