// Package duckduckgo implements the DuckDuckGo web search engine.
//
// Port of searx/engines/duckduckgo.py. Uses the DDG HTML (no-JS) endpoint.
// For the initial version, only first-page results are supported since
// subsequent pages require VQD token caching.
package duckduckgo

import (
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"golang.org/x/net/html"

	"github.com/searxng/searxng-go/internal/config"
	"github.com/searxng/searxng-go/internal/engine"
	"github.com/searxng/searxng-go/internal/result"
)

const ddgURL = "https://html.duckduckgo.com/html/"

var timeRangeMap = map[string]string{
	"day":   "d",
	"week":  "w",
	"month": "m",
	"year":  "y",
}

type DuckDuckGo struct {
	cfg config.EngineConfig
}

func New(cfg config.EngineConfig) (engine.Engine, error) {
	return &DuckDuckGo{cfg: cfg}, nil
}

func (d *DuckDuckGo) Name() string             { return d.cfg.Name }
func (d *DuckDuckGo) Categories() []string      { return d.cfg.Categories }
func (d *DuckDuckGo) Shortcut() string          { return d.cfg.Shortcut }
func (d *DuckDuckGo) SupportsPaging() bool      { return false } // VQD caching needed for paging
func (d *DuckDuckGo) SupportsTimeRange() bool   { return true }
func (d *DuckDuckGo) SupportsSafeSearch() bool  { return false }
func (d *DuckDuckGo) MaxPage() int              { return 1 }

func (d *DuckDuckGo) BuildRequest(query string, params *engine.SearchParams) (*http.Request, error) {
	if len(query) >= 500 {
		return nil, fmt.Errorf("query too long for DDG (max 499 chars)")
	}

	formData := url.Values{}
	formData.Set("q", query)
	formData.Set("b", "")
	formData.Set("kl", "wt-wt") // default: all regions

	if params.Language != "" && params.Language != "auto" && params.Language != "all" {
		// DDG uses region codes like "us-en", "uk-en", "de-de"
		formData.Set("kl", mapLanguage(params.Language))
	}

	if tr, ok := timeRangeMap[params.TimeRange]; ok {
		formData.Set("df", tr)
	}

	req, err := http.NewRequest("POST", ddgURL, strings.NewReader(formData.Encode()))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("Referer", "https://html.duckduckgo.com/")
	req.Header.Set("Sec-Fetch-Dest", "document")
	req.Header.Set("Sec-Fetch-Mode", "navigate")
	req.Header.Set("Sec-Fetch-Site", "same-origin")
	req.Header.Set("Sec-Fetch-User", "?1")

	return req, nil
}

func (d *DuckDuckGo) ParseResponse(resp *http.Response, body []byte) ([]result.Result, error) {
	doc, err := html.Parse(strings.NewReader(string(body)))
	if err != nil {
		return nil, fmt.Errorf("parsing HTML: %w", err)
	}

	var results []result.Result

	// DDG HTML results are in: <div id="links"> / <div class="web-result">
	var walk func(*html.Node)
	walk = func(n *html.Node) {
		if isWebResult(n) {
			if r, ok := parseWebResult(n); ok {
				results = append(results, r)
			}
		} else {
			for c := n.FirstChild; c != nil; c = c.NextSibling {
				walk(c)
			}
		}
	}
	walk(doc)

	return results, nil
}

func isWebResult(n *html.Node) bool {
	if n.Type != html.ElementNode || n.Data != "div" {
		return false
	}
	class := getAttr(n, "class")
	return strings.Contains(class, "web-result") && !strings.Contains(class, "result--ad")
}

func parseWebResult(div *html.Node) (result.Result, bool) {
	// Find <h2><a href="...">title</a></h2>
	var titleLink *html.Node
	findH2Link(div, &titleLink)
	if titleLink == nil {
		return result.Result{}, false
	}

	href := getAttr(titleLink, "href")
	title := extractText(titleLink)
	if href == "" || title == "" {
		return result.Result{}, false
	}

	// Find content snippet: <a class="result__snippet">
	content := findSnippet(div)

	return result.Result{
		URL:      href,
		Title:    title,
		Content:  content,
		Category: "general",
		Template: "default",
		Priority: "normal",
	}, true
}

func findH2Link(n *html.Node, result **html.Node) {
	if n.Type == html.ElementNode && n.Data == "h2" {
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			if c.Type == html.ElementNode && c.Data == "a" {
				*result = c
				return
			}
		}
	}
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		findH2Link(c, result)
		if *result != nil {
			return
		}
	}
}

func findSnippet(n *html.Node) string {
	if n.Type == html.ElementNode && n.Data == "a" {
		class := getAttr(n, "class")
		if strings.Contains(class, "result__snippet") {
			return extractText(n)
		}
	}
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		if s := findSnippet(c); s != "" {
			return s
		}
	}
	return ""
}

func mapLanguage(lang string) string {
	// Simple mapping: "en" -> "us-en", "de" -> "de-de", etc.
	lang = strings.ToLower(lang)
	if strings.Contains(lang, "-") {
		parts := strings.SplitN(lang, "-", 2)
		return parts[1] + "-" + parts[0]
	}
	switch lang {
	case "en":
		return "us-en"
	default:
		return lang + "-" + lang
	}
}

func getAttr(n *html.Node, key string) string {
	for _, a := range n.Attr {
		if a.Key == key {
			return a.Val
		}
	}
	return ""
}

func extractText(n *html.Node) string {
	if n.Type == html.TextNode {
		return n.Data
	}
	var sb strings.Builder
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		if c.Type == html.ElementNode && (c.Data == "script" || c.Data == "style") {
			continue
		}
		sb.WriteString(extractText(c))
	}
	return strings.TrimSpace(sb.String())
}

func init() {
	engine.Register("duckduckgo", New)
}
