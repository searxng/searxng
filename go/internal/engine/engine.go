// Package engine defines the Engine interface and search parameter types.
package engine

import (
	"net/http"

	"github.com/searxng/searxng-go/internal/result"
)

// SearchParams holds parameters passed to an engine's BuildRequest method.
type SearchParams struct {
	Query      string
	Language   string
	SafeSearch int // 0=off, 1=moderate, 2=strict
	PageNo     int
	TimeRange  string // "", "day", "week", "month", "year"
	Category   string
	EngineData map[string]string
}

// Engine is the interface that all search engine backends must implement.
type Engine interface {
	// Metadata
	Name() string
	Categories() []string
	Shortcut() string

	// Capabilities
	SupportsPaging() bool
	SupportsTimeRange() bool
	SupportsSafeSearch() bool
	MaxPage() int

	// Search lifecycle for online engines.
	// BuildRequest prepares an HTTP request for the upstream engine.
	BuildRequest(query string, params *SearchParams) (*http.Request, error)

	// ParseResponse parses the upstream response body into results.
	ParseResponse(resp *http.Response, body []byte) ([]result.Result, error)
}
