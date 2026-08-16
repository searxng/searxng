// SPDX-License-Identifier: AGPL-3.0-or-later

import { Plugin } from "../Plugin.ts";
import { settings } from "../toolkit.ts";
import { assertElement } from "../util/assertElement.ts";

type Message = { role: "user" | "assistant"; content: string };
type ContextItem = { title: string; url: string; snippet: string };
type StreamLine = { delta?: string; done?: boolean; model?: string; error?: string };

// keep in sync with the server side defaults (searx/ai_summary.py)
const MAX_CONTEXT_ITEMS = 5;
const MAX_HISTORY_MESSAGES = 12;
const MAX_TITLE_LENGTH = 300;
const MAX_SNIPPET_LENGTH = 1000;

/**
 * Fills the AI summary placeholder (rendered by the ai_summary plugin of the
 * server) by streaming an answer from the /ai_summary endpoint, with an
 * expand button and a follow-up question chat.
 */
export default class AiSummary extends Plugin {
  private readonly messages: Message[] = [];
  private context: ContextItem[] = [];
  private controller: AbortController | undefined;

  public constructor() {
    super("ai_summary");
  }

  protected async run(): Promise<void> {
    const box = document.getElementById("ai_summary");
    if (!box) return;

    try {
      const { query } = box.dataset;
      if (!query) return;

      if (box.dataset.grounding === "1") {
        this.context = AiSummary.collectContext();
      }

      this.wireControls(box);

      this.messages.push({ role: "user", content: query });
      await this.exchange(box);
    } catch (error) {
      // never fail silently, always leave a message in the summary box
      AiSummary.showError(box, error);
    }
  }

  protected async post(): Promise<void> {
    // noop
  }

  /**
   * Scrape the top search results from the DOM as grounding context.
   */
  private static collectContext(): ContextItem[] {
    const items: ContextItem[] = [];
    for (const article of document.querySelectorAll<HTMLElement>("#urls article.result")) {
      if (items.length >= MAX_CONTEXT_ITEMS) break;

      const link = article.querySelector<HTMLAnchorElement>("h3 a");
      if (!link) continue;

      items.push({
        title: (link.textContent ?? "").trim().slice(0, MAX_TITLE_LENGTH),
        url: link.href,
        snippet: (article.querySelector(".content")?.textContent ?? "").trim().slice(0, MAX_SNIPPET_LENGTH)
      });
    }
    return items;
  }

  private wireControls(box: HTMLElement): void {
    const body = box.querySelector<HTMLElement>(".ai-summary-body");
    const moreButton = box.querySelector<HTMLElement>(".ai-summary-more");
    const followupForm = box.querySelector<HTMLFormElement>(".ai-summary-followup");
    assertElement(body);
    assertElement(moreButton);
    assertElement(followupForm);

    moreButton.addEventListener("click", () => {
      const collapsed = body.classList.toggle("collapsed");
      moreButton.textContent = collapsed
        ? (moreButton.dataset.btnTextCollapsed ?? "")
        : (moreButton.dataset.btnTextNotCollapsed ?? "");
      followupForm.classList.toggle("invisible", collapsed);
    });

    followupForm.addEventListener("submit", (event: Event) => {
      event.preventDefault();

      const input = followupForm.querySelector<HTMLInputElement>("input");
      assertElement(input);

      const question = input.value.trim();
      if (!question || this.controller) return;

      input.value = "";
      this.messages.push({ role: "user", content: question });
      // the server rejects too long histories, drop the oldest messages
      this.messages.splice(0, this.messages.length - (MAX_HISTORY_MESSAGES - 1));

      const questionElement = Object.assign(document.createElement("p"), {
        textContent: question,
        className: "ai-summary-question"
      });
      box.querySelector(".ai-summary-answers")?.append(questionElement);

      void this.exchange(box);
    });
  }

  /**
   * Send the message history to /ai_summary and stream the answer into a new
   * block in the answer area.
   */
  private async exchange(box: HTMLElement): Promise<void> {
    const answers = box.querySelector<HTMLElement>(".ai-summary-answers");
    assertElement(answers);

    const block = Object.assign(document.createElement("p"), {
      className: "ai-summary-content typing"
    });
    answers.append(block);

    const controller = new AbortController();
    this.controller = controller;

    let text = "";
    const handleLine = (line: string): void => {
      if (!line.trim()) return;

      const data = JSON.parse(line) as StreamLine;
      if (data.error) {
        throw new Error(data.error);
      }
      if (data.delta) {
        text += data.delta;
        block.textContent = text;
        this.updateMoreButton(box);
      }
      if (data.done && data.model) {
        const modelElement = box.querySelector<HTMLElement>(".ai-summary-model");
        if (modelElement) modelElement.textContent = data.model;
      }
    };

    try {
      const res = await fetch("./ai_summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: this.messages, context: this.context }),
        signal: controller.signal
      });
      if (!res.ok) {
        // the status is shown to the user: it is often the only thing
        // available to diagnose a failure on a device without dev tools
        throw new Error(`HTTP ${res.status}`);
      }

      if (res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        for (;;) {
          // biome-ignore lint/performance/noAwaitInLoops: chunks of a stream are read sequentially
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";
          for (const line of lines) handleLine(line);
        }
        handleLine(buffer);
      } else {
        // some webviews (e.g. Brave iOS) wrap fetch and don't expose a
        // streaming body: no typing effect, render the answer in one go
        const body = await res.text();
        for (const line of body.split("\n")) handleLine(line);
      }
      this.messages.push({ role: "assistant", content: text });
    } catch (error) {
      AiSummary.showError(box, error);
    } finally {
      block.classList.remove("typing");
      this.controller = undefined;
      this.updateMoreButton(box);
    }
  }

  private static showError(box: HTMLElement, error: unknown): void {
    console.error("Error loading AI summary:", error);

    const message = settings.translations?.error_loading_ai_summary ?? "Error loading the AI summary";
    const reason = error instanceof Error && error.message ? ` (${error.message})` : "";

    const errorElement = Object.assign(document.createElement("div"), {
      textContent: `${message}${reason}`,
      className: "dialog-error"
    });
    errorElement.setAttribute("role", "alert");
    (box.querySelector<HTMLElement>(".ai-summary-answers") ?? box).append(errorElement);
  }

  /**
   * Show the expand button as soon as the (collapsed) body overflows.
   */
  private updateMoreButton(box: HTMLElement): void {
    const body = box.querySelector<HTMLElement>(".ai-summary-body");
    const moreButton = box.querySelector<HTMLElement>(".ai-summary-more");
    if (!(body && moreButton)) return;

    if (!body.classList.contains("collapsed") || body.scrollHeight > body.clientHeight + 4) {
      moreButton.classList.remove("invisible");
    }
  }
}
