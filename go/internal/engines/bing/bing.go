// Package bing implements the Bing web search engine.
//
// Port of searx/engines/bing.py. Parses HTML results from Bing's search page.
package bing

import (
	"encoding/base64"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"golang.org/x/net/html"

	"github.com/searxng/searxng-go/internal/config"
	"github.com/searxng/searxng-go/internal/engine"
	"github.com/searxng/searxng-go/internal/result"
)

var safeSearchMap = map[int]string{
	0: "off",
	1: "moderate",
	2: "strict",
}

type Bing struct {
	cfg config.EngineConfig
}

func New(cfg config.EngineConfig) (engine.Engine, error) {
	return &Bing{cfg: cfg}, nil
}

func (b *Bing) Name() string             { return b.cfg.Name }
func (b *Bing) Categories() []string      { return b.cfg.Categories }
func (b *Bing) Shortcut() string          { return b.cfg.Shortcut }
func (b *Bing) SupportsPaging() bool      { return false }
func (b *Bing) SupportsTimeRange() bool   { return false }
func (b *Bing) SupportsSafeSearch() bool  { return true }
func (b *Bing) MaxPage() int              { return 1 }

func (b *Bing) BuildRequest(query string, params *engine.SearchParams) (*http.Request, error) {
	q := url.Values{}
	q.Set("q", query)

	ss := safeSearchMap[params.SafeSearch]
	if ss == "" {
		ss = "off"
	}
	q.Set("adlt", ss)

	// Set market based on language.
	if params.Language != "" && params.Language != "auto" && params.Language != "all" {
		q.Set("mkt", params.Language)
	}

	reqURL := "https://www.bing.com/search?" + q.Encode()

	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")
	return req, nil
}

func (b *Bing) ParseResponse(resp *http.Response, body []byte) ([]result.Result, error) {
	doc, err := html.Parse(strings.NewReader(string(body)))
	if err != nil {
		return nil, fmt.Errorf("parsing HTML: %w", err)
	}

	var results []result.Result

	// Find result items: <li class="b_algo"> inside <ol id="b_results">
	var walk func(*html.Node)
	walk = func(n *html.Node) {
		if isResultItem(n) {
			if r, ok := parseResultItem(n); ok {
				results = append(results, r)
			}
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			walk(c)
		}
	}
	walk(doc)

	return results, nil
}

// isResultItem checks if a node is <li class="b_algo">.
func isResultItem(n *html.Node) bool {
	if n.Type != html.ElementNode || n.Data != "li" {
		return false
	}
	class := getAttr(n, "class")
	return strings.Contains(class, "b_algo")
}

func parseResultItem(li *html.Node) (result.Result, bool) {
	// Find <h2><a href="...">title</a></h2>
	var linkNode *html.Node
	findLink(li, &linkNode)
	if linkNode == nil {
		return result.Result{}, false
	}

	href := getAttr(linkNode, "href")
	title := extractText(linkNode)
	if href == "" || title == "" {
		return result.Result{}, false
	}

	// Decode Bing redirect URLs: https://www.bing.com/ck/a?u=a1<base64url>
	href = decodeBingURL(href)

	// Find content in <p> elements.
	content := findParagraphText(li)

	return result.Result{
		URL:      href,
		Title:    title,
		Content:  content,
		Category: "general",
		Template: "default",
		Priority: "normal",
	}, true
}

// decodeBingURL decodes Bing's redirect tracking URLs.
// Matches the Python logic at bing.py:141-151.
func decodeBingURL(href string) string {
	if !strings.HasPrefix(href, "https://www.bing.com/ck/a?") {
		return href
	}
	u, err := url.Parse(href)
	if err != nil {
		return href
	}
	uVal := u.Query().Get("u")
	if uVal == "" || !strings.HasPrefix(uVal, "a1") {
		return href
	}
	encoded := uVal[2:]
	// base64url without padding
	if m := len(encoded) % 4; m != 0 {
		encoded += strings.Repeat("=", 4-m)
	}
	decoded, err := base64.URLEncoding.DecodeString(encoded)
	if err != nil {
		return href
	}
	return string(decoded)
}

func findLink(n *html.Node, result **html.Node) {
	if n.Type == html.ElementNode && n.Data == "h2" {
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			if c.Type == html.ElementNode && c.Data == "a" {
				*result = c
				return
			}
		}
	}
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		findLink(c, result)
		if *result != nil {
			return
		}
	}
}

func findParagraphText(n *html.Node) string {
	if n.Type == html.ElementNode && n.Data == "p" {
		return extractText(n)
	}
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		if text := findParagraphText(c); text != "" {
			return text
		}
	}
	return ""
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
	engine.Register("bing", New)
}
