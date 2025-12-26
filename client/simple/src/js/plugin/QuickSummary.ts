// SPDX-License-Identifier: AGPL-3.0-or-later

import { Plugin } from "../Plugin.ts";
import { http } from "../toolkit.ts";
import { getElement } from "../util/getElement.ts";

/**
 * Async loading of AI-powered Quick Summary.
 */
export default class QuickSummary extends Plugin {
  protected constructor() {
    super("quickSummary");
  }

  protected async run(): Promise<boolean> {
    const summaryElement = getElement<HTMLElement>("quick_summary");
    if (!summaryElement) return false;

    const bodyElement = summaryElement.querySelector<HTMLElement>(".quick-summary-body");
    if (!bodyElement) return false;

    // Extract query and results data from DOM
    const queryInput = document.querySelector<HTMLInputElement>("#q");
    const query = queryInput?.value?.trim();
    
    // Get top N results based on settings
    const maxResults = (window as any).quick_summary_max_results || 10;
    const resultElements = Array.from(document.querySelectorAll<HTMLElement>("#urls article.result"))
      .slice(0, maxResults);

    if (!query || resultElements.length === 0) return false;

    const results = resultElements.map((el, idx) => ({
      index: idx,
      title: el.querySelector(".result_title a")?.textContent || el.querySelector("h3")?.textContent || '',
      url: el.querySelector(".result_title a")?.href || el.querySelector("a")?.href || '',
      content: el.querySelector(".content")?.textContent || ''
    }));

    try {
      // Call async endpoint
      const res = await http("POST", "/quick_summary", {
        body: JSON.stringify({ q: query, results }),
        timeout: 35000
      });

      const data = await res.json();

      if (data.error) {
        this.showError(data.error);
      } else {
        this.renderSummary(data);
      }
    } catch (error) {
      console.error("Quick Summary error:", error);
      this.showError("Failed to generate summary. Please try again.");
    }

    return true;
  }

  protected async post(_result: boolean): Promise<void> {
    // Register collapse button handler
    const collapseBtn = document.getElementById("collapse_quick_summary");
    collapseBtn?.addEventListener("click", () => {
      const summaryElement = document.getElementById("quick_summary");
      summaryElement?.classList.toggle("collapsed");
      const icon = collapseBtn.querySelector("svg");
      if (summaryElement?.classList.contains("collapsed")) {
        icon?.classList.add("rotate-180");
      } else {
        icon?.classList.remove("rotate-180");
      }
    });

    // Register retry button handler
    const retryBtn = document.getElementById("retry_quick_summary");
    retryBtn?.addEventListener("click", () => {
      void this.run();
    });
  }

  private renderSummary(data: any): void {
    const summaryElement = document.getElementById("quick_summary");
    const bodyElement = summaryElement?.querySelector<HTMLElement>(".quick-summary-body");
    
    if (!bodyElement) return;

    // Format summary with clickable citations
    const formattedSummary = this.formatWithCitations(data.summary, data.citations);
    
    // Build citations list HTML
    let citationsHtml = '';
    if (data.citations && data.citations.length > 0) {
      const translations = (window as any).translations || {};
      citationsHtml = `
        <div class="quick-summary-citations">
          <h5>${translations.Sources || 'Sources'}</h5>
          <ul>
            ${data.citations.map((c: any, i: number) => `
              <li>
                <sup><a href="#result-${c.result_index}" class="citation-link">[${c.index}]</a></sup>
                <a href="#result-${c.result_index}" class="citation-title">${this.escapeHtml(c.title)}</a>
              </li>
            `).join('')}
          </ul>
        </div>
      `;
    }

    bodyElement.innerHTML = `
      <div class="quick-summary-content">
        <div class="quick-summary-text">
          ${formattedSummary}
        </div>
        ${citationsHtml}
      </div>
    `;

    // Scroll to first citation when clicked
    bodyElement.querySelectorAll<HTMLElement>(".citation-link").forEach(link => {
      link.addEventListener("click", (e) => {
        const targetId = link.getAttribute("href");
        if (targetId?.startsWith("#result-")) {
          e.preventDefault();
          const targetElement = document.querySelector<HTMLElement>(targetId);
          targetElement?.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    });
  }

  private formatWithCitations(text: string, citations: any[]): string {
    if (!citations || citations.length === 0) return this.escapeHtml(text);

    // Replace [1], [2], etc. with clickable citation links
    let formatted = this.escapeHtml(text);
    
    citations.forEach((c: any) => {
      const citationPattern = new RegExp(`\\[${c.index}\\]`, 'g');
      formatted = formatted.replace(citationPattern, 
        `<a href="#result-${c.result_index}" class="citation-link">[${c.index}]</a>`
      );
    });

    return formatted;
  }

  private showError(message: string): void {
    const summaryElement = document.getElementById("quick_summary");
    const bodyElement = summaryElement?.querySelector<HTMLElement>(".quick-summary-body");
    
    if (!bodyElement) return;

    bodyElement.innerHTML = `
      <div class="quick-summary-error" role="alert">
        <p>${this.escapeHtml(message)}</p>
        <button id="retry_quick_summary" type="button">
          ${this.escapeHtml((window as any).translations?.Retry || 'Retry')}
        </button>
      </div>
    `;
    
    // Re-register retry button for new error state
    document.getElementById("retry_quick_summary")?.addEventListener("click", () => {
      void this.run();
    });
  }

  private escapeHtml(text: string): string {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
}
