// Package brave implements the Brave web search engine.
//
// Port of searx/engines/brave.py. Queries Brave's search page
// and parses results from the embedded JSON data or HTML.
package brave

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

var timeRangeMap = map[string]string{
	"day":   "pd",
	"week":  "pw",
	"month": "pm",
	"year":  "py",
}

var safeSearchMap = map[int]string{
	0: "off",
	1: "moderate",
	2: "strict",
}

type Brave struct {
	cfg config.EngineConfig
}

func New(cfg config.EngineConfig) (engine.Engine, error) {
	return &Brave{cfg: cfg}, nil
}

func (b *Brave) Name() string             { return b.cfg.Name }
func (b *Brave) Categories() []string      { return b.cfg.Categories }
func (b *Brave) Shortcut() string          { return b.cfg.Shortcut }
func (b *Brave) SupportsPaging() bool      { return true }
func (b *Brave) SupportsTimeRange() bool   { return true }
func (b *Brave) SupportsSafeSearch() bool  { return true }
func (b *Brave) MaxPage() int              { return 10 }

func (b *Brave) BuildRequest(query string, params *engine.SearchParams) (*http.Request, error) {
	q := url.Values{}
	q.Set("q", query)
	q.Set("source", "web")

	if params.PageNo > 1 {
		q.Set("offset", fmt.Sprintf("%d", params.PageNo-1))
	}
	if tr, ok := timeRangeMap[params.TimeRange]; ok {
		q.Set("tf", tr)
	}

	reqURL := "https://search.brave.com/search?" + q.Encode()

	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
	req.Header.Set("Accept-Encoding", "gzip, deflate")

	// Set cookies.
	ss := safeSearchMap[params.SafeSearch]
	if ss == "" {
		ss = "off"
	}
	req.AddCookie(&http.Cookie{Name: "safesearch", Value: ss})
	req.AddCookie(&http.Cookie{Name: "useLocation", Value: "0"})
	req.AddCookie(&http.Cookie{Name: "summarizer", Value: "0"})

	return req, nil
}

func (b *Brave) ParseResponse(resp *http.Response, body []byte) ([]result.Result, error) {
	doc, err := html.Parse(strings.NewReader(string(body)))
	if err != nil {
		return nil, fmt.Errorf("parsing HTML: %w", err)
	}

	var results []result.Result

	// Brave results are in <div class="snippet" data-type="web">
	var walk func(*html.Node)
	walk = func(n *html.Node) {
		if isSnippet(n) {
			if r, ok := parseSnippet(n); ok {
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

func isSnippet(n *html.Node) bool {
	if n.Type != html.ElementNode || n.Data != "div" {
		return false
	}
	class := getAttr(n, "class")
	return strings.Contains(class, "snippet") && getAttr(n, "data-type") == "web"
}

func parseSnippet(div *html.Node) (result.Result, bool) {
	// Find title link: <a class="result-header">
	var titleNode *html.Node
	var contentText string

	var walk func(*html.Node)
	walk = func(n *html.Node) {
		if n.Type == html.ElementNode && n.Data == "a" {
			class := getAttr(n, "class")
			if strings.Contains(class, "result-header") || strings.Contains(class, "heading") {
				titleNode = n
			}
		}
		if n.Type == html.ElementNode {
			class := getAttr(n, "class")
			if strings.Contains(class, "snippet-description") || strings.Contains(class, "snippet-content") {
				text := extractText(n)
				if len(text) > len(contentText) {
					contentText = text
				}
			}
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			walk(c)
		}
	}
	walk(div)

	if titleNode == nil {
		return result.Result{}, false
	}

	href := getAttr(titleNode, "href")
	title := extractText(titleNode)
	if href == "" || title == "" {
		return result.Result{}, false
	}

	return result.Result{
		URL:      href,
		Title:    title,
		Content:  contentText,
		Category: "general",
		Template: "default",
		Priority: "normal",
	}, true
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
	engine.Register("brave", New)
}
