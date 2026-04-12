// Package google implements the Google web search engine.
//
// This is a simplified port of searx/engines/google.py. It queries
// Google's search page and parses the HTML results.
package google

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
	"day":   "d",
	"week":  "w",
	"month": "m",
	"year":  "y",
}

var safeSearchMap = map[int]string{
	0: "off",
	1: "medium",
	2: "high",
}

// Google implements the Engine interface for Google web search.
type Google struct {
	cfg config.EngineConfig
}

func New(cfg config.EngineConfig) (engine.Engine, error) {
	return &Google{cfg: cfg}, nil
}

func (g *Google) Name() string             { return g.cfg.Name }
func (g *Google) Categories() []string      { return g.cfg.Categories }
func (g *Google) Shortcut() string          { return g.cfg.Shortcut }
func (g *Google) SupportsPaging() bool      { return true }
func (g *Google) SupportsTimeRange() bool   { return true }
func (g *Google) SupportsSafeSearch() bool  { return true }
func (g *Google) MaxPage() int              { return 50 }

func (g *Google) BuildRequest(query string, params *engine.SearchParams) (*http.Request, error) {
	start := (params.PageNo - 1) * 10

	q := url.Values{}
	q.Set("q", query)
	q.Set("hl", "en")
	q.Set("lr", "")
	q.Set("ie", "utf8")
	q.Set("oe", "utf8")
	q.Set("filter", "0")
	q.Set("start", fmt.Sprintf("%d", start))

	if params.Language != "" && params.Language != "auto" && params.Language != "all" {
		lang := params.Language
		if idx := strings.Index(lang, "-"); idx > 0 {
			lang = lang[:idx]
		}
		q.Set("hl", lang)
		q.Set("lr", "lang_"+lang)
	}

	if tr, ok := timeRangeMap[params.TimeRange]; ok {
		q.Set("tbs", "qdr:"+tr)
	}
	if ss, ok := safeSearchMap[params.SafeSearch]; ok && params.SafeSearch > 0 {
		q.Set("safe", ss)
	}

	reqURL := "https://www.google.com/search?" + q.Encode()

	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Accept", "*/*")
	req.Header.Set("Cookie", "CONSENT=YES+")
	return req, nil
}

func (g *Google) ParseResponse(resp *http.Response, body []byte) ([]result.Result, error) {
	doc, err := html.Parse(strings.NewReader(string(body)))
	if err != nil {
		return nil, fmt.Errorf("parsing HTML: %w", err)
	}

	var results []result.Result

	// Walk the DOM looking for result links.
	// Google results are typically <a> tags with data-ved attribute.
	var walk func(*html.Node)
	walk = func(n *html.Node) {
		if n.Type == html.ElementNode && n.Data == "a" {
			href := getAttr(n, "href")
			dataVed := getAttr(n, "data-ved")

			if dataVed != "" && href != "" && !strings.HasPrefix(href, "#") {
				// Clean up Google redirect URLs.
				actualURL := href
				if strings.HasPrefix(href, "/url?q=") {
					if u, err := url.Parse(href); err == nil {
						if q := u.Query().Get("q"); q != "" {
							actualURL = q
						}
					}
				}

				// Skip internal google links.
				if strings.HasPrefix(actualURL, "/") || strings.Contains(actualURL, "google.com/search") {
					goto children
				}

				title := extractText(n)
				if title == "" {
					goto children
				}

				// Try to find content in sibling/parent nodes.
				content := ""
				if parent := n.Parent; parent != nil {
					if grandparent := parent.Parent; grandparent != nil {
						content = findContent(grandparent)
					}
				}

				results = append(results, result.Result{
					URL:      actualURL,
					Title:    title,
					Content:  content,
					Category: "general",
					Template: "default",
					Priority: "normal",
				})
			}
		}
	children:
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			walk(c)
		}
	}
	walk(doc)

	return results, nil
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

func findContent(n *html.Node) string {
	// Look for content-like text in descendant elements.
	var best string
	var walk func(*html.Node)
	walk = func(node *html.Node) {
		if node.Type == html.ElementNode && (node.Data == "span" || node.Data == "div") {
			text := extractText(node)
			if len(text) > len(best) && len(text) > 20 {
				best = text
			}
		}
		for c := node.FirstChild; c != nil; c = c.NextSibling {
			walk(c)
		}
	}
	walk(n)
	return best
}

func init() {
	engine.Register("google", New)
}
