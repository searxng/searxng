// Package wikipedia implements the Wikipedia search engine.
//
// Port of searx/engines/wikipedia.py. Uses the Wikipedia REST v1 summary API.
// This is a clean JSON API, no HTML parsing needed.
package wikipedia

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"github.com/searxng/searxng-go/internal/config"
	"github.com/searxng/searxng-go/internal/engine"
	"github.com/searxng/searxng-go/internal/result"
)

const summaryURLTemplate = "https://%s.wikipedia.org/api/rest_v1/page/summary/%s"

type Wikipedia struct {
	cfg config.EngineConfig
}

func New(cfg config.EngineConfig) (engine.Engine, error) {
	return &Wikipedia{cfg: cfg}, nil
}

func (w *Wikipedia) Name() string             { return w.cfg.Name }
func (w *Wikipedia) Categories() []string      { return w.cfg.Categories }
func (w *Wikipedia) Shortcut() string          { return w.cfg.Shortcut }
func (w *Wikipedia) SupportsPaging() bool      { return false }
func (w *Wikipedia) SupportsTimeRange() bool   { return false }
func (w *Wikipedia) SupportsSafeSearch() bool  { return false }
func (w *Wikipedia) MaxPage() int              { return 1 }

func (w *Wikipedia) BuildRequest(query string, params *engine.SearchParams) (*http.Request, error) {
	// Title-case the query for better Wikipedia matching.
	if strings.ToLower(query) == query {
		query = strings.Title(query) //nolint:staticcheck
	}

	lang := "en"
	if params.Language != "" && params.Language != "auto" && params.Language != "all" {
		lang = params.Language
		if idx := strings.Index(lang, "-"); idx > 0 {
			lang = lang[:idx]
		}
	}

	title := url.PathEscape(query)
	reqURL := fmt.Sprintf(summaryURLTemplate, lang, title)

	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Accept", "application/json")
	return req, nil
}

// apiResponse maps the Wikipedia REST v1 summary response.
type apiResponse struct {
	Type        string `json:"type"`
	Title       string `json:"title"`
	DisplayTitle string `json:"displaytitle"`
	Titles      struct {
		Display string `json:"display"`
	} `json:"titles"`
	Extract     string `json:"extract"`
	Description string `json:"description"`
	ContentURLs struct {
		Desktop struct {
			Page string `json:"page"`
		} `json:"desktop"`
	} `json:"content_urls"`
	Thumbnail struct {
		Source string `json:"source"`
	} `json:"thumbnail"`
}

func (w *Wikipedia) ParseResponse(resp *http.Response, body []byte) ([]result.Result, error) {
	if resp.StatusCode == 404 || resp.StatusCode == 400 {
		return nil, nil // No results, not an error.
	}
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("wikipedia API returned %d", resp.StatusCode)
	}

	var api apiResponse
	if err := json.Unmarshal(body, &api); err != nil {
		return nil, fmt.Errorf("parsing wikipedia JSON: %w", err)
	}

	pageURL := api.ContentURLs.Desktop.Page
	if pageURL == "" {
		return nil, nil
	}

	title := api.Titles.Display
	if title == "" {
		title = api.Title
	}

	var results []result.Result
	results = append(results, result.Result{
		URL:       pageURL,
		Title:     title,
		Content:   api.Description,
		Thumbnail: api.Thumbnail.Source,
		Category:  "general",
		Template:  "default",
		Priority:  "normal",
	})

	return results, nil
}

func init() {
	engine.Register("wikipedia", New)
}
