// Package server provides the HTTP server and JSON API routes.
package server

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"

	"github.com/searxng/searxng-go/internal/config"
	"github.com/searxng/searxng-go/internal/engine"
	"github.com/searxng/searxng-go/internal/network"
	"github.com/searxng/searxng-go/internal/query"
	"github.com/searxng/searxng-go/internal/search"
)

// Server is the SearXNG HTTP server.
type Server struct {
	cfg         *config.Config
	engines     map[string]engine.Engine
	client      *network.Client
	suspensions map[string]*network.SuspendedStatus
	categories  map[string]bool
	router      chi.Router
}

// New creates a new Server.
func New(cfg *config.Config, engines map[string]engine.Engine, client *network.Client) *Server {
	s := &Server{
		cfg:         cfg,
		engines:     engines,
		client:      client,
		suspensions: make(map[string]*network.SuspendedStatus),
		categories:  make(map[string]bool),
	}

	// Build category set and suspension trackers.
	for _, ecfg := range cfg.Engines {
		if ecfg.Disabled || ecfg.Inactive {
			continue
		}
		for _, cat := range ecfg.Categories {
			s.categories[cat] = true
		}
		s.suspensions[ecfg.Name] = network.NewSuspendedStatus(
			30*time.Second, 10*time.Minute,
		)
	}

	s.router = s.buildRouter()
	return s
}

func (s *Server) buildRouter() chi.Router {
	r := chi.NewRouter()
	r.Use(middleware.RealIP)
	r.Use(middleware.Recoverer)
	if s.cfg.General.Debug {
		r.Use(middleware.Logger)
	}

	r.Get("/healthz", s.handleHealthz)
	r.Get("/config", s.handleConfig)
	r.Get("/search", s.handleSearch)
	r.Post("/search", s.handleSearch)
	return r
}

// ListenAndServe starts the HTTP server.
func (s *Server) ListenAndServe() error {
	addr := fmt.Sprintf("%s:%d", s.cfg.Server.BindAddress, s.cfg.Server.Port)
	slog.Info("starting server", "addr", addr)
	return http.ListenAndServe(addr, s.router)
}

// handleHealthz returns a simple health check.
func (s *Server) handleHealthz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

// handleConfig returns instance configuration.
func (s *Server) handleConfig(w http.ResponseWriter, r *http.Request) {
	type engineInfo struct {
		Name       string   `json:"name"`
		Shortcut   string   `json:"shortcut"`
		Categories []string `json:"categories"`
		Enabled    bool     `json:"enabled"`
	}

	var engineList []engineInfo
	for _, ecfg := range s.cfg.Engines {
		if ecfg.Inactive {
			continue
		}
		engineList = append(engineList, engineInfo{
			Name:       ecfg.Name,
			Shortcut:   ecfg.Shortcut,
			Categories: ecfg.Categories,
			Enabled:    !ecfg.Disabled,
		})
	}

	cats := make([]string, 0, len(s.categories))
	for c := range s.categories {
		cats = append(cats, c)
	}

	resp := map[string]any{
		"instance_name": s.cfg.General.InstanceName,
		"engines":       engineList,
		"categories":    cats,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// handleSearch parses query params and executes a search.
func (s *Server) handleSearch(w http.ResponseWriter, r *http.Request) {
	q := r.FormValue("q")
	if q == "" {
		writeError(w, http.StatusBadRequest, "missing required parameter: q")
		return
	}

	pageno := parseIntParam(r, "pageno", 1)
	if pageno < 1 {
		writeError(w, http.StatusBadRequest, "pageno must be >= 1")
		return
	}

	safesearch := parseIntParam(r, "safesearch", s.cfg.Search.SafeSearch)
	if safesearch < 0 || safesearch > 2 {
		writeError(w, http.StatusBadRequest, "safesearch must be 0, 1, or 2")
		return
	}

	timeRange := r.FormValue("time_range")
	if timeRange != "" && timeRange != "day" && timeRange != "week" &&
		timeRange != "month" && timeRange != "year" {
		writeError(w, http.StatusBadRequest, "time_range must be day, week, month, or year")
		return
	}

	language := r.FormValue("language")
	if language == "" {
		language = s.cfg.Search.DefaultLang
	}

	timeoutLimit := parseFloatParam(r, "timeout_limit", s.cfg.Outgoing.MaxRequestTimeout)
	if timeoutLimit > s.cfg.Outgoing.MaxRequestTimeout && s.cfg.Outgoing.MaxRequestTimeout > 0 {
		timeoutLimit = s.cfg.Outgoing.MaxRequestTimeout
	}

	// Parse query for bangs and language overrides.
	parsed := query.Parse(q, s.engines, s.categories)
	if parsed.Language != "" {
		language = parsed.Language
	}

	// Resolve which engines to search.
	refs := s.resolveEngineRefs(r, parsed)
	if len(refs) == 0 {
		writeError(w, http.StatusBadRequest, "no engines selected for the given categories")
		return
	}

	sq := search.Query{
		Query:        parsed.Query,
		EngineRefs:   refs,
		Lang:         language,
		SafeSearch:   safesearch,
		PageNo:       pageno,
		TimeRange:    timeRange,
		TimeoutLimit: time.Duration(timeoutLimit * float64(time.Second)),
	}

	ctx := r.Context()
	resp := search.Execute(ctx, sq, s.engines, s.client, s.suspensions)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// resolveEngineRefs determines which engines to query based on request params and parsed query.
func (s *Server) resolveEngineRefs(r *http.Request, parsed query.Parsed) []search.EngineRef {
	var refs []search.EngineRef

	// Explicit engines from query param.
	if enginesParam := r.FormValue("engines"); enginesParam != "" {
		for _, name := range strings.Split(enginesParam, ",") {
			name = strings.TrimSpace(name)
			if eng, ok := s.engines[name]; ok {
				cats := eng.Categories()
				cat := "general"
				if len(cats) > 0 {
					cat = cats[0]
				}
				refs = append(refs, search.EngineRef{Name: name, Category: cat})
			}
		}
		return refs
	}

	// Engines/categories from bang syntax in query.
	if len(parsed.Engines) > 0 {
		for _, name := range parsed.Engines {
			if eng, ok := s.engines[name]; ok {
				cats := eng.Categories()
				cat := "general"
				if len(cats) > 0 {
					cat = cats[0]
				}
				refs = append(refs, search.EngineRef{Name: name, Category: cat})
			}
		}
		return refs
	}

	// Categories from bang syntax or query param.
	selectedCats := parsed.Categories
	if len(selectedCats) == 0 {
		if catParam := r.FormValue("categories"); catParam != "" {
			selectedCats = strings.Split(catParam, ",")
			for i := range selectedCats {
				selectedCats[i] = strings.TrimSpace(selectedCats[i])
			}
		}
	}
	if len(selectedCats) == 0 {
		selectedCats = []string{"general"}
	}

	catSet := make(map[string]bool, len(selectedCats))
	for _, c := range selectedCats {
		catSet[c] = true
	}

	// Select all active engines matching the categories.
	for _, ecfg := range s.cfg.Engines {
		if ecfg.Disabled || ecfg.Inactive {
			continue
		}
		if _, ok := s.engines[ecfg.Name]; !ok {
			continue
		}
		for _, cat := range ecfg.Categories {
			if catSet[cat] {
				refs = append(refs, search.EngineRef{Name: ecfg.Name, Category: cat})
				break
			}
		}
	}

	return refs
}

func writeError(w http.ResponseWriter, code int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(map[string]string{"error": msg})
}

func parseIntParam(r *http.Request, name string, defaultVal int) int {
	s := r.FormValue(name)
	if s == "" {
		return defaultVal
	}
	v, err := strconv.Atoi(s)
	if err != nil {
		return defaultVal
	}
	return v
}

func parseFloatParam(r *http.Request, name string, defaultVal float64) float64 {
	s := r.FormValue(name)
	if s == "" {
		return defaultVal
	}
	v, err := strconv.ParseFloat(s, 64)
	if err != nil {
		return defaultVal
	}
	return v
}

// Handler returns the http.Handler for use in tests.
func (s *Server) Handler() http.Handler {
	return s.router
}

// Shutdown gracefully shuts down the server.
func (s *Server) Shutdown(ctx context.Context) error {
	// The chi router doesn't need cleanup, but this is where
	// we'd close the HTTP server if using http.Server directly.
	return nil
}
