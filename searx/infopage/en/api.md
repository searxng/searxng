# Search API

This instance exposes a JSON API for programmatic access. It is configured to
return results from **Saudi Arabian sources** in Arabic (`ar-SA`) by default.

An AI-readable summary is always available at [/llms.txt].

---

## Endpoint

```
GET /search
```

| Parameter    | Required | Description |
|--------------|----------|-------------|
| `q`          | yes      | Search query (Arabic or English) |
| `format`     | no       | `json` for machine-readable output (default: `html`) |
| `categories` | no       | `general` for web search (default: `general`) |
| `language`   | no       | Locale code — `ar-SA` targets Saudi Arabia (default: `ar-SA`) |

---

## Finding a company's official website

**Arabic query:**

```
/search?q=أرامكو+السعودية+الموقع+الرسمي&format=json&categories=general&language=ar-SA
```

**English query:**

```
/search?q=Saudi+Aramco+official+website&format=json&categories=general&language=ar-SA
```

---

## JSON response structure

```json
{
  "query": "Saudi Aramco",
  "results": [
    {
      "url": "https://www.aramco.com",
      "title": "Saudi Aramco",
      "content": "The world's largest oil company...",
      "engine": "google",
      "score": 1.0
    }
  ]
}
```

Extract `results[].url` for the company website. The first result is usually
the official site.

---

## Notes

- **CORS** is enabled (`Access-Control-Allow-Origin: *`) — call from any origin.
- No authentication or API key required.
- Active engines: Google, Bing, DuckDuckGo (all use the `ar-SA` region).
- Results are not cached per-request; each call queries live search engines.

[/llms.txt]: /llms.txt
