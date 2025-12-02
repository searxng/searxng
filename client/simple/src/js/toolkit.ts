// SPDX-License-Identifier: AGPL-3.0-or-later

import type { KeyBindingLayout } from "./main/keyboard.ts";

// synced with searx/webapp.py get_client_settings
type Settings = {
  plugins?: string[];
  advanced_search?: boolean;
  autocomplete?: string;
  autocomplete_min?: number;
  doi_resolver?: string;
  favicon_resolver?: string;
  hotkeys?: KeyBindingLayout;
  method?: "GET" | "POST";
  query_in_title?: boolean;
  results_on_new_tab?: boolean;
  safesearch?: 0 | 1 | 2;
  search_on_category_select?: boolean;
  theme?: string;
  theme_static_path?: string;
  translations?: Record<string, string>;
  url_formatting?: "pretty" | "full" | "host";
};

type HTTPOptions = {
  body?: BodyInit;
  timeout?: number;
};

type ReadyOptions = {
  // all values must be truthy for the callback to be executed
  on?: (boolean | undefined)[];
};

export type EndpointsKeys = keyof typeof Endpoints;

export const Endpoints = {
  index: "index",
  results: "results",
  preferences: "preferences",
  unknown: "unknown"
} as const;

export const mutable = {
  closeDetail: undefined as (() => void) | undefined,
  scrollPageToSelected: undefined as (() => void) | undefined,
  selectImage: undefined as ((resultElement: HTMLElement) => void) | undefined,
  selectNext: undefined as ((openDetailView?: boolean) => void) | undefined,
  selectPrevious: undefined as ((openDetailView?: boolean) => void) | undefined
};

const getEndpoint = (): EndpointsKeys => {
  const metaEndpoint = document.querySelector('meta[name="endpoint"]')?.getAttribute("content");

  if (metaEndpoint && metaEndpoint in Endpoints) {
    return metaEndpoint as EndpointsKeys;
  }

  return Endpoints.unknown;
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

export const http = async (method: string, url: string | URL, options?: HTTPOptions): Promise<Response> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options?.timeout ?? 30_000);

  const res = await fetch(url, {
    body: options?.body,
    method: method,
    signal: controller.signal
  }).finally(() => clearTimeout(timeoutId));
  if (!res.ok) {
    throw new Error(res.statusText);
  }

  return res;
};

export const listen = <K extends keyof DocumentEventMap, E extends HTMLElement>(
  type: string | K,
  target: string | Document | E,
  listener: (this: E, event: DocumentEventMap[K]) => void | Promise<void>,
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
        if (node instanceof HTMLElement && node.matches(target)) {
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
};

export const ready = (callback: () => void, options?: ReadyOptions): void => {
  for (const condition of options?.on ?? []) {
    if (!condition) {
      return;
    }
  }

  if (document.readyState !== "loading") {
    callback();
  } else {
    listen("DOMContentLoaded", document, callback, { once: true });
  }
};

export const endpoint: EndpointsKeys = getEndpoint();
export const settings: Settings = getSettings();
