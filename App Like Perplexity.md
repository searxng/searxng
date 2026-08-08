If you want to build a **Perplexity-like app**, don't think of it as “one model.” Perplexity is essentially a **search + retrieval + ranking + LLM generation system**.

For your app, I would build the stack like this:

### Recommended architecture

```text
User question
     ↓
Query understanding / router
     ↓
Web Search
     ↓
Fetch webpages
     ↓
Clean + extract content
     ↓
Reranker
     ↓
Top relevant passages
     ↓
LLM
     ↓
Answer + citations
```

### Models I would choose

| Job                     | Model                    | Why                               |
| ----------------------- | ------------------------ | --------------------------------- |
| 🧠 Main answer model    | **Qwen3.5 27B**          | Excellent quality/size balance    |
| ⚡ Fast/simple questions | **Qwen3.5 9B**           | Fast and relatively cheap         |
| 🧩 Query classification | **Qwen3.5 4B/9B**        | Decides what the user wants       |
| 🔎 Embeddings           | **Qwen3-Embedding-8B**   | Strong semantic retrieval         |
| 🎯 Reranking            | **Qwen3-Reranker-4B/8B** | Selects the most relevant sources |
| 🖼️ Image understanding | **Qwen3.5 multimodal**   | Understands images/screenshots    |
| 💻 Coding               | **Qwen3.5 27B**          | Strong coding capability          |
| 📝 Summarization        | **Qwen3.5 9B**           | Fast enough for many documents    |

**If you want to keep everything open-source/open-weight, Qwen is currently one of the best ecosystems to build around.**

### But you ALSO need search

The LLM itself doesn't magically know today's internet.

For example:

> **User:** "What happened in the latest OpenAI release?"

Your system should do:

```text
Question
   ↓
Search engine
   ↓
10–20 web results
   ↓
Download pages
   ↓
Extract text
   ↓
Qwen Reranker
   ↓
Top 5 sources
   ↓
Qwen 27B
   ↓
"According to [Source 1]..."
```

For search, you can use:

* **SearXNG** — open-source metasearch
* **Brave Search API**
* **Bing Search API**
* **Google Programmable Search**
* **Tavily**
* **Exa**

If your goal is to make a **fully self-hosted/open-source Perplexity**, I'd use **SearXNG + your own crawler/parser**.

---

## 💡 What I'd build for your project

Since you already work with **Python, React/React Native, MongoDB and AI**, I'd use:

```text
                 ┌──────────────┐
                 │ React / RN   │
                 │   Frontend   │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ FastAPI      │
                 │ Backend      │
                 └──────┬───────┘
                        ↓
              ┌───────────────────┐
              │   AI Router       │
              └─────────┬─────────┘
                        ↓
             ┌────────────────────┐
             │    Web Search      │
             │     SearXNG        │
             └─────────┬──────────┘
                       ↓
             ┌────────────────────┐
             │ Page extraction    │
             │ Trafilatura        │
             │ BeautifulSoup      │
             └─────────┬──────────┘
                       ↓
             ┌────────────────────┐
             │ Qwen Reranker      │
             └─────────┬──────────┘
                       ↓
             ┌────────────────────┐
             │ Qwen 3.5 27B       │
             │ Answer generation  │
             └─────────┬──────────┘
                       ↓
             ┌────────────────────┐
             │ Answer + Citations │
             └────────────────────┘
```

### For the database

I'd use:

**MongoDB**

for:

* users
* conversations
* messages
* search history
* source metadata
* saved pages

And:

**Qdrant**

for:

* embeddings
* semantic search
* RAG
* conversation memory

---

# If you have limited hardware

This is where I would start:

### 🟢 Minimum setup

```text
Qwen3.5 9B
       +
Qwen Embedding
       +
Qwen Reranker
       +
SearXNG
       +
Qdrant
```

You can build a surprisingly capable Perplexity-style application with this.

### 🟡 Better setup

```text
Qwen3.5 27B
       +
Qwen3 Embedding
       +
Qwen3 Reranker
       +
SearXNG
       +
Qdrant
```

This is what I'd personally choose for a serious prototype.

### 🔴 High-end

```text
Qwen 3.5 122B
        +
Embedding 8B
        +
Reranker 8B
        +
SearXNG
        +
Qdrant
```

Much better answer quality, but hardware requirements become substantial.

---

## One more important component: citations

This is what makes your app feel like **Perplexity rather than ChatGPT with a search button**.

Your backend should return something like:

```json
{
  "answer": "OpenAI announced ...",
  "sources": [
    {
      "title": "OpenAI announcement",
      "url": "...",
      "snippet": "...",
      "published": "2026-08-08"
    },
    {
      "title": "TechCrunch",
      "url": "...",
      "snippet": "...",
      "published": "2026-08-08"
    }
  ]
}
```

Then your UI can display:

> OpenAI announced X on August 8, 2026. **[1]**

and underneath:

```text
Sources

[1] OpenAI — Official announcement
[2] TechCrunch — Analysis
[3] The Verge — Coverage
```

You should also make the model **cite claims against retrieved passages**, rather than allowing it to invent URLs.

---

### My recommended MVP

If I were building this with you, I'd start with:

**Qwen3.5 9B → search → rerank → Qwen3.5 27B → citations**

rather than immediately trying to run a 100B+ model.

That gives you a manageable system where you can first get the **Perplexity experience** working, then upgrade the model later without redesigning the application.
