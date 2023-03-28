document.addEventListener('DOMContentLoaded', () => {
  const chatgptApiKey = '{{ chatgpt_api_key_var }}';
  const query = '{{ q }}';
  const gptResultsContent = document.getElementById('gptResultsContent');

  if (chatgptApiKey && query && gptResultsContent) {
    fetchGPTResults(chatgptApiKey, query).then((results) => {
      if (results) {
        gptResultsContent.innerHTML = results;
      }
    });
  }
});

async function fetchGPTResults(apiKey, query) {
  const apiEndpoint = 'https://api.openai.com/v1/engines/davinci-codex/completions';
  const prompt = `Generate a brief summary for the following search query: ${query}`;

  try {
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        prompt: prompt,
        max_tokens: 50,
        n: 1,
        stop: null,
        temperature: 0.5,
      }),
    });

    const data = await response.json();
    if (data.choices && data.choices.length > 0) {
      return data.choices[0].text.trim();
    }
  } catch (error) {
    console.error('Error fetching GPT-3.5 Turbo results:', error);
  }

  return null;
}
