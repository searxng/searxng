package server

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/searxng/searxng-go/internal/config"
	"github.com/searxng/searxng-go/internal/engine"
	"github.com/searxng/searxng-go/internal/network"
	"github.com/searxng/searxng-go/internal/result"
)

// mockEngine is a test engine that returns canned results.
type mockEngine struct {
	name string
}

func (m *mockEngine) Name() string             { return m.name }
func (m *mockEngine) Categories() []string      { return []string{"general"} }
func (m *mockEngine) Shortcut() string          { return "mk" }
func (m *mockEngine) SupportsPaging() bool      { return false }
func (m *mockEngine) SupportsTimeRange() bool   { return false }
func (m *mockEngine) SupportsSafeSearch() bool  { return false }
func (m *mockEngine) MaxPage() int              { return 1 }

func (m *mockEngine) BuildRequest(query string, params *engine.SearchParams) (*http.Request, error) {
	// Return a request that will be handled by a test server.
	return http.NewRequest("GET", "http://invalid.test/search?q="+query, nil)
}

func (m *mockEngine) ParseResponse(resp *http.Response, body []byte) ([]result.Result, error) {
	return []result.Result{
		{
			URL:      "https://example.com/result",
			Title:    "Test Result",
			Content:  "This is a test result",
			Template: "default",
			Priority: "normal",
			Weight:   1.0,
		},
	}, nil
}

func TestHealthzEndpoint(t *testing.T) {
	srv := newTestServer()
	req := httptest.NewRequest("GET", "/healthz", nil)
	w := httptest.NewRecorder()

	srv.Handler().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var body map[string]string
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if body["status"] != "ok" {
		t.Errorf("expected status ok, got %q", body["status"])
	}
}

func TestConfigEndpoint(t *testing.T) {
	srv := newTestServer()
	req := httptest.NewRequest("GET", "/config", nil)
	w := httptest.NewRecorder()

	srv.Handler().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var body map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if body["instance_name"] != "Test Instance" {
		t.Errorf("expected instance name 'Test Instance', got %v", body["instance_name"])
	}
}

func TestSearchMissingQuery(t *testing.T) {
	srv := newTestServer()
	req := httptest.NewRequest("GET", "/search", nil)
	w := httptest.NewRecorder()

	srv.Handler().ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", w.Code)
	}
}

func TestSearchInvalidParams(t *testing.T) {
	srv := newTestServer()

	tests := []struct {
		name string
		url  string
	}{
		{"bad pageno", "/search?q=test&pageno=-1"},
		{"bad safesearch", "/search?q=test&safesearch=5"},
		{"bad time_range", "/search?q=test&time_range=invalid"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", tt.url, nil)
			w := httptest.NewRecorder()
			srv.Handler().ServeHTTP(w, req)

			if w.Code != http.StatusBadRequest {
				t.Errorf("expected 400, got %d", w.Code)
			}
		})
	}
}

func TestSearchReturnsJSON(t *testing.T) {
	srv := newTestServer()
	req := httptest.NewRequest("GET", "/search?q=hello", nil)
	w := httptest.NewRecorder()

	srv.Handler().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	contentType := w.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected application/json, got %s", contentType)
	}

	var body map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}

	// Should have the standard response fields.
	for _, key := range []string{"query", "results", "answers", "corrections", "suggestions", "unresponsive_engines"} {
		if _, ok := body[key]; !ok {
			t.Errorf("missing response field %q", key)
		}
	}

	if body["query"] != "hello" {
		t.Errorf("expected query 'hello', got %v", body["query"])
	}
}

func newTestServer() *Server {
	cfg := &config.Config{
		General: config.GeneralConfig{
			Debug:        false,
			InstanceName: "Test Instance",
		},
		Search: config.SearchConfig{
			SafeSearch:  0,
			DefaultLang: "en",
		},
		Server: config.ServerConfig{
			Port:        8888,
			BindAddress: "127.0.0.1",
		},
		Outgoing: config.OutgoingConfig{
			RequestTimeout:    3.0,
			MaxRequestTimeout: 10.0,
			MaxConnections:    10,
			MaxIdleConns:      5,
		},
		Engines: []config.EngineConfig{
			{
				Name:       "mock",
				Engine:     "mock",
				Shortcut:   "mk",
				Categories: []string{"general"},
				Timeout:    3.0,
				Weight:     1.0,
			},
		},
	}

	engines := map[string]engine.Engine{
		"mock": &mockEngine{name: "mock"},
	}
	client := network.NewClient(cfg.Outgoing)
	return New(cfg, engines, client)
}
