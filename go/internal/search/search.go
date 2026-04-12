// Package search orchestrates parallel engine dispatch and result collection.
package search

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"golang.org/x/sync/errgroup"

	"github.com/searxng/searxng-go/internal/engine"
	"github.com/searxng/searxng-go/internal/network"
	"github.com/searxng/searxng-go/internal/result"
)

// Query holds the parameters for a search operation.
type Query struct {
	Query        string
	EngineRefs   []EngineRef
	Lang         string
	SafeSearch   int
	PageNo       int
	TimeRange    string
	TimeoutLimit time.Duration
	EngineData   map[string]map[string]string
}

// EngineRef identifies an engine and category to search.
type EngineRef struct {
	Name     string
	Category string
}

// Response is the complete search response.
type Response struct {
	Query               string                     `json:"query"`
	NumberOfResults     int                        `json:"number_of_results"`
	Results             []result.Result            `json:"results"`
	Answers             []result.Answer            `json:"answers"`
	Corrections         []string                   `json:"corrections"`
	Infoboxes           []map[string]any           `json:"infoboxes"`
	Suggestions         []string                   `json:"suggestions"`
	UnresponsiveEngines []result.UnresponsiveEngine `json:"unresponsive_engines"`
}

// Execute runs a search across the specified engines in parallel.
func Execute(
	ctx context.Context,
	q Query,
	engines map[string]engine.Engine,
	client *network.Client,
	suspensions map[string]*network.SuspendedStatus,
) *Response {

	container := result.NewContainer()
	timeout := q.TimeoutLimit
	if timeout <= 0 {
		timeout = 5 * time.Second
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	g, ctx := errgroup.WithContext(ctx)

	for _, ref := range q.EngineRefs {
		eng, ok := engines[ref.Name]
		if !ok {
			slog.Warn("engine not found", "name", ref.Name)
			continue
		}

		// Check suspension.
		if s, ok := suspensions[ref.Name]; ok && s.IsSuspended() {
			container.AddUnresponsive(ref.Name, "suspended", true)
			continue
		}

		g.Go(func() error {
			searchEngine(ctx, eng, q, ref, client, container, suspensions)
			return nil // never propagate errors; we record them in container
		})
	}

	_ = g.Wait()

	results := container.GetOrderedResults()
	if results == nil {
		results = []result.Result{}
	}
	return &Response{
		Query:               q.Query,
		NumberOfResults:     len(results),
		Results:             results,
		Answers:             orEmpty(container.Answers),
		Corrections:         orEmptyStr(container.Corrections),
		Infoboxes:           orEmptyInfobox(container.Infoboxes),
		Suggestions:         orEmptyStr(container.Suggestions),
		UnresponsiveEngines: orEmptyUnresponsive(container.Unresponsive),
	}
}

func searchEngine(
	ctx context.Context,
	eng engine.Engine,
	q Query,
	ref EngineRef,
	client *network.Client,
	container *result.Container,
	suspensions map[string]*network.SuspendedStatus,
) {
	start := time.Now()
	name := eng.Name()

	params := &engine.SearchParams{
		Query:      q.Query,
		Language:   q.Lang,
		SafeSearch: q.SafeSearch,
		PageNo:     q.PageNo,
		TimeRange:  q.TimeRange,
		Category:   ref.Category,
	}
	if ed, ok := q.EngineData[name]; ok {
		params.EngineData = ed
	}

	// Check capabilities.
	if q.PageNo > 1 && !eng.SupportsPaging() {
		return
	}
	if q.PageNo > eng.MaxPage() && eng.MaxPage() > 0 {
		return
	}
	if q.TimeRange != "" && !eng.SupportsTimeRange() {
		// Still search, just ignore time_range.
		params.TimeRange = ""
	}

	req, err := eng.BuildRequest(q.Query, params)
	if err != nil {
		slog.Error("engine build request failed", "engine", name, "error", err)
		container.AddUnresponsive(name, fmt.Sprintf("build request: %v", err), false)
		recordError(suspensions, name)
		return
	}

	resp, body, err := client.Do(ctx, req)
	if err != nil {
		slog.Error("engine http request failed", "engine", name,
			"error", err, "duration", time.Since(start))
		container.AddUnresponsive(name, fmt.Sprintf("http error: %v", err), false)
		recordError(suspensions, name)
		return
	}

	// Classify HTTP errors.
	if engErr := network.ClassifyHTTPError(resp, body); engErr != nil {
		slog.Warn("engine returned error", "engine", name,
			"kind", engErr.Kind, "msg", engErr.Message)
		container.AddUnresponsive(name, engErr.Message, false)
		recordError(suspensions, name)
		return
	}

	results, err := eng.ParseResponse(resp, body)
	if err != nil {
		slog.Error("engine parse response failed", "engine", name, "error", err)
		container.AddUnresponsive(name, fmt.Sprintf("parse error: %v", err), false)
		recordError(suspensions, name)
		return
	}

	// Set weight from engine config on each result.
	container.AddResults(results, name)
	recordSuccess(suspensions, name)

	slog.Debug("engine search complete", "engine", name,
		"results", len(results), "duration", time.Since(start))
}

func recordError(suspensions map[string]*network.SuspendedStatus, name string) {
	if s, ok := suspensions[name]; ok {
		s.RecordError()
	}
}

func recordSuccess(suspensions map[string]*network.SuspendedStatus, name string) {
	if s, ok := suspensions[name]; ok {
		s.RecordSuccess()
	}
}

// Helper functions to ensure JSON arrays are never null.
func orEmpty(a []result.Answer) []result.Answer {
	if a == nil {
		return []result.Answer{}
	}
	return a
}

func orEmptyStr(a []string) []string {
	if a == nil {
		return []string{}
	}
	return a
}

func orEmptyInfobox(a []map[string]any) []map[string]any {
	if a == nil {
		return []map[string]any{}
	}
	return a
}

func orEmptyUnresponsive(a []result.UnresponsiveEngine) []result.UnresponsiveEngine {
	if a == nil {
		return []result.UnresponsiveEngine{}
	}
	return a
}
