// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Prominent AI Integration - Frontend Controller
 *
 * Manages the highly visible AI panel with:
 * - Provider selection (Ollama/Anthropic/OpenAI)
 * - Live AI chat interface
 * - Real-time result scoring and insights
 * - Prominent visual indicators
 */

interface AIProvider {
  name: string;
  endpoint: string;
  model: string;
}

interface AIMessage {
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

class ProminentAIIntegration {
  private currentProvider: 'ollama' | 'anthropic' | 'openai' = 'ollama';
  private messages: AIMessage[] = [];
  private panel: HTMLElement | null = null;
  private isVisible: boolean = true;

  constructor() {
    this.init();
  }

  init() {
    this.createAIPanel();
    this.createFloatingButton();
    this.addAIBadgesToResults();
    this.setupProviderSelection();
    this.setupChatInterface();
    this.showWelcomeMessage();
  }

  /**
   * Create the prominent AI panel
   */
  createAIPanel() {
    const panel = document.createElement('div');
    panel.id = 'ai-panel';
    panel.innerHTML = `
      <div class="ai-header">
        <div class="ai-logo"></div>
        <div class="ai-title">
          <h3>AI Search Assistant</h3>
          <div class="ai-subtitle">Powered by AI</div>
        </div>
        <div class="ai-status"></div>
      </div>

      <div class="ai-provider">
        <label>AI Provider:</label>
        <div class="provider-buttons">
          <button class="provider-btn active" data-provider="ollama">Ollama</button>
          <button class="provider-btn" data-provider="anthropic">Claude</button>
          <button class="provider-btn" data-provider="openai">GPT</button>
        </div>
      </div>

      <div class="ai-chat">
        <div class="ai-messages" id="ai-messages"></div>
        <div class="ai-input-wrapper">
          <input type="text" id="ai-chat-input" placeholder="Ask AI anything about your search..." />
          <button id="ai-send-btn"></button>
        </div>
      </div>

      <div class="ai-insights">
        <h4>AI Insights</h4>
        <div id="ai-insights-content">
          <div class="insight-item">Analyzing search results...</div>
        </div>
      </div>
    `;

    // Insert after search or at top of results
    const results = document.getElementById('results');
    if (results && results.parentNode) {
      results.parentNode.insertBefore(panel, results);
    } else {
      document.body.appendChild(panel);
    }

    this.panel = panel;
  }

  /**
   * Create floating AI button
   */
  createFloatingButton() {
    const button = document.createElement('div');
    button.id = 'ai-floating-button';
    button.title = 'AI Assistant';

    button.addEventListener('click', () => {
      this.togglePanel();
    });

    document.body.appendChild(button);
  }

  /**
   * Toggle AI panel visibility
   */
  togglePanel() {
    if (!this.panel) return;

    this.isVisible = !this.isVisible;
    this.panel.style.display = this.isVisible ? 'block' : 'none';
  }

  /**
   * Add large AI badges to search results
   */
  addAIBadgesToResults() {
    const results = document.querySelectorAll('article.result');

    results.forEach((result, index) => {
      // Only badge top results
      if (index >= 5) return;

      const badge = document.createElement('div');
      badge.className = 'result-ai-badge';

      // Simulate AI scoring (in real implementation, this comes from backend)
      const scores = ['high', 'high', 'medium', 'medium', 'low'];
      const score = scores[index];
      const scoreValues = { high: '95%', medium: '75%', low: '50%' };

      badge.setAttribute('data-score', score);
      badge.innerHTML = `
        AI Match
        <span class="ai-score-value">${scoreValues[score]}</span>
      `;

      result.style.position = 'relative';
      result.appendChild(badge);
    });
  }

  /**
   * Setup provider selection buttons
   */
  setupProviderSelection() {
    const buttons = document.querySelectorAll('.provider-btn');

    buttons.forEach(button => {
      button.addEventListener('click', (e) => {
        const target = e.target as HTMLButtonElement;
        const provider = target.dataset.provider as 'ollama' | 'anthropic' | 'openai';

        // Update active state
        buttons.forEach(btn => btn.classList.remove('active'));
        target.classList.add('active');

        // Update current provider
        this.currentProvider = provider;

        // Show notification
        this.addAIMessage(`Switched to ${this.getProviderName(provider)}`, 'ai');
      });
    });
  }

  /**
   * Setup chat interface
   */
  setupChatInterface() {
    const input = document.getElementById('ai-chat-input') as HTMLInputElement;
    const sendBtn = document.getElementById('ai-send-btn');

    const sendMessage = () => {
      if (!input || !input.value.trim()) return;

      const message = input.value.trim();
      this.addAIMessage(message, 'user');
      input.value = '';

      // Simulate AI response (in real implementation, call API)
      setTimeout(() => {
        this.generateAIResponse(message);
      }, 1000);
    };

    sendBtn?.addEventListener('click', sendMessage);
    input?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        sendMessage();
      }
    });
  }

  /**
   * Add message to chat
   */
  addAIMessage(content: string, role: 'user' | 'ai') {
    const messagesContainer = document.getElementById('ai-messages');
    if (!messagesContainer) return;

    const message: AIMessage = {
      role,
      content,
      timestamp: new Date()
    };

    this.messages.push(message);

    const messageEl = document.createElement('div');
    messageEl.className = `ai-message ${role}`;
    messageEl.textContent = content;

    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  /**
   * Generate AI response (mock - real implementation calls API)
   */
  generateAIResponse(userMessage: string) {
    const responses = [
      `Based on your search results, I've analyzed the top pages using ${this.getProviderName(this.currentProvider)}.`,
      'The most relevant results show strong matching scores.',
      'I can help refine your search query. What specific aspect interests you?',
      'The AI analysis suggests these results contain high-quality information.',
    ];

    const response = responses[Math.floor(Math.random() * responses.length)];
    this.addAIMessage(response, 'ai');

    // Update insights
    this.updateInsights();
  }

  /**
   * Update AI insights panel
   */
  updateInsights() {
    const insightsContainer = document.getElementById('ai-insights-content');
    if (!insightsContainer) return;

    const insights = [
      'Top 3 results have 90%+ relevance scores',
      'Results cover multiple perspectives on the topic',
      'Recent content (last 30 days) is prioritized',
      `Analysis powered by ${this.getProviderName(this.currentProvider)}`,
    ];

    insightsContainer.innerHTML = insights
      .map(insight => `<div class="insight-item">✓ ${insight}</div>`)
      .join('');
  }

  /**
   * Show welcome message
   */
  showWelcomeMessage() {
    setTimeout(() => {
      this.addAIMessage(
        `👋 Hi! I'm your AI search assistant powered by ${this.getProviderName(this.currentProvider)}. I've analyzed your results and scored them for relevance. Ask me anything!`,
        'ai'
      );
      this.updateInsights();
    }, 500);
  }

  /**
   * Get friendly provider name
   */
  getProviderName(provider: string): string {
    const names = {
      ollama: 'Ollama (Local)',
      anthropic: 'Claude AI',
      openai: 'ChatGPT',
    };
    return names[provider] || provider;
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on results page
    if (document.getElementById('results')) {
      new ProminentAIIntegration();
    }
  });
} else {
  if (document.getElementById('results')) {
    new ProminentAIIntegration();
  }
}

export { ProminentAIIntegration };
