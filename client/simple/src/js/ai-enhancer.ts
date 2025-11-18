// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * AI Enhancer Frontend
 *
 * Handles display of AI-enhanced features:
 * - Relevance scores
 * - Result summaries
 * - Interactive blob-wave cursor follower
 */

interface BlobWavePosition {
  x: number;
  y: number;
}

class AIEnhancer {
  private interactiveBlob: HTMLElement | null = null;
  private currentPosition: BlobWavePosition = { x: 0, y: 0 };
  private targetPosition: BlobWavePosition = { x: 0, y: 0 };

  constructor() {
    this.init();
  }

  init() {
    this.enhanceResults();
    this.createInteractiveBlob();
    this.setupEventListeners();
  }

  /**
   * Enhance search results with AI features
   */
  enhanceResults() {
    const results = document.querySelectorAll('article.result');

    results.forEach((result) => {
      const resultData = this.getResultData(result as HTMLElement);

      if (resultData.aiScore) {
        this.addRelevanceScore(result as HTMLElement, resultData.aiScore);
      }

      if (resultData.aiSummary) {
        this.addSummary(result as HTMLElement, resultData.aiSummary);
      }
    });
  }

  /**
   * Extract AI data from result element
   */
  getResultData(result: HTMLElement): { aiScore?: string; aiSummary?: string } {
    // In a real implementation, this would parse data attributes
    // For now, we'll look for data attributes that the backend might add
    return {
      aiScore: result.dataset.aiScore,
      aiSummary: result.dataset.aiSummary,
    };
  }

  /**
   * Add relevance score badge to result
   */
  addRelevanceScore(result: HTMLElement, score: string) {
    const scoreElement = document.createElement('div');
    scoreElement.className = `ai-relevance-score`;
    scoreElement.setAttribute('data-score', score);

    const indicator = document.createElement('span');
    indicator.className = 'score-indicator';

    const label = document.createElement('span');
    label.textContent = `${score.charAt(0).toUpperCase() + score.slice(1)} Relevance`;

    scoreElement.appendChild(indicator);
    scoreElement.appendChild(label);

    // Insert at the beginning of the result
    const firstChild = result.querySelector('h3, .result-title');
    if (firstChild) {
      firstChild.parentNode?.insertBefore(scoreElement, firstChild);
    }
  }

  /**
   * Add AI summary to result
   */
  addSummary(result: HTMLElement, summary: string) {
    const summaryElement = document.createElement('div');
    summaryElement.className = 'ai-summary';

    const label = document.createElement('div');
    label.className = 'ai-summary-label';
    label.textContent = 'AI Summary';

    const text = document.createElement('div');
    text.className = 'ai-summary-text';
    text.textContent = summary;

    summaryElement.appendChild(label);
    summaryElement.appendChild(text);

    // Insert after content
    const content = result.querySelector('.content');
    if (content) {
      content.parentNode?.insertBefore(summaryElement, content.nextSibling);
    }
  }

  /**
   * Create interactive blob that follows cursor
   */
  createInteractiveBlob() {
    // Only on desktop
    if (window.innerWidth < 768) {
      return;
    }

    const blob = document.createElement('div');
    blob.className = 'blob-wave-interactive';
    document.body.appendChild(blob);

    this.interactiveBlob = blob;

    // Start animation loop
    this.animateBlob();
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    if (!this.interactiveBlob) return;

    // Track cursor movement
    document.addEventListener('mousemove', (e) => {
      this.targetPosition = {
        x: e.clientX,
        y: e.clientY,
      };
    });

    // Hide blob when cursor leaves window
    document.addEventListener('mouseleave', () => {
      if (this.interactiveBlob) {
        this.interactiveBlob.style.opacity = '0';
      }
    });

    document.addEventListener('mouseenter', () => {
      if (this.interactiveBlob) {
        this.interactiveBlob.style.opacity = '0.2';
      }
    });
  }

  /**
   * Animate interactive blob with smooth following
   */
  animateBlob() {
    if (!this.interactiveBlob) return;

    // Smooth easing
    const ease = 0.15;

    this.currentPosition.x += (this.targetPosition.x - this.currentPosition.x) * ease;
    this.currentPosition.y += (this.targetPosition.y - this.currentPosition.y) * ease;

    // Update position (centered on cursor)
    this.interactiveBlob.style.transform = `translate(${this.currentPosition.x - 150}px, ${this.currentPosition.y - 150}px)`;

    // Continue animation
    requestAnimationFrame(() => this.animateBlob());
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new AIEnhancer();
  });
} else {
  new AIEnhancer();
}

export { AIEnhancer };
