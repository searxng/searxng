// Package result defines search result types, deduplication, merging, and scoring.
package result

import (
	"fmt"
	"net/url"
	"strings"
	"time"
)

// Result represents a single search result from an engine.
type Result struct {
	URL           string     `json:"url"`
	Title         string     `json:"title"`
	Content       string     `json:"content"`
	Engine        string     `json:"engine"`
	Engines       []string   `json:"engines"`
	Score         float64    `json:"score"`
	Category      string     `json:"category"`
	Positions     []int      `json:"positions"`
	PublishedDate *time.Time `json:"publishedDate,omitempty"`
	Thumbnail     string     `json:"thumbnail,omitempty"`
	ImgSrc        string     `json:"img_src,omitempty"`
	Author        string     `json:"author,omitempty"`
	Metadata      string     `json:"metadata,omitempty"`
	Template      string     `json:"-"`
	Priority      string     `json:"-"` // "low", "normal", "high"
	Weight        float64    `json:"-"` // inherited from engine config
}

// Answer represents an instant answer.
type Answer struct {
	Answer string `json:"answer"`
	URL    string `json:"url,omitempty"`
}

// Suggestion is a search suggestion string.
type Suggestion = string

// Correction is a spelling correction string.
type Correction = string

// UnresponsiveEngine records an engine that failed during search.
type UnresponsiveEngine struct {
	Engine    string `json:"engine"`
	Error     string `json:"error"`
	Suspended bool   `json:"suspended"`
}

// Hash returns a deduplication key for the result.
// Matches the Python logic: hash on template + URL (without scheme) + img_src.
func (r *Result) Hash() string {
	parsed, err := url.Parse(r.URL)
	if err != nil {
		return r.URL
	}
	tmpl := r.Template
	if tmpl == "" {
		tmpl = "default"
	}
	return fmt.Sprintf("%s|%s|%s|%s|%s|%s|%s",
		tmpl,
		parsed.Host,
		parsed.Path,
		parsed.RawQuery,
		parsed.Fragment,
		parsed.User,
		r.ImgSrc,
	)
}

// Merge combines another result into this one (dedup merge).
// Keeps the longer title/content, unions engines, prefers HTTPS.
func (r *Result) Merge(other *Result) {
	if len(other.Title) > len(r.Title) {
		r.Title = other.Title
	}
	if len(other.Content) > len(r.Content) {
		r.Content = other.Content
	}

	// Prefer HTTPS
	if strings.HasPrefix(other.URL, "https://") && strings.HasPrefix(r.URL, "http://") {
		r.URL = other.URL
	}

	// Union engines
	seen := make(map[string]bool, len(r.Engines))
	for _, e := range r.Engines {
		seen[e] = true
	}
	for _, e := range other.Engines {
		if !seen[e] {
			r.Engines = append(r.Engines, e)
		}
	}

	// Accumulate positions
	r.Positions = append(r.Positions, other.Positions...)

	// Keep non-empty optional fields
	if r.Thumbnail == "" {
		r.Thumbnail = other.Thumbnail
	}
	if r.ImgSrc == "" {
		r.ImgSrc = other.ImgSrc
	}
	if r.Author == "" {
		r.Author = other.Author
	}
	if r.PublishedDate == nil {
		r.PublishedDate = other.PublishedDate
	}
}

// CalculateScore computes the result score based on positions, weight, and priority.
// Matches the Python scoring at searx/results.py:17-38.
func (r *Result) CalculateScore() {
	weight := r.Weight
	if weight <= 0 {
		weight = 1.0
	}

	var score float64
	for _, pos := range r.Positions {
		switch r.Priority {
		case "high":
			score += weight
		case "low":
			// score += 0
		default: // "normal" or empty
			if pos > 0 {
				score += weight / float64(pos)
			}
		}
	}

	r.Score = score
}
