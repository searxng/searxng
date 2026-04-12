// Package query parses raw search query text, extracting bang commands,
// language selectors, and the cleaned query string.
package query

import (
	"strings"

	"github.com/searxng/searxng-go/internal/engine"
)

// Parsed is the result of parsing a raw query string.
type Parsed struct {
	Query      string   // cleaned query text with bangs/lang removed
	Engines    []string // explicitly selected engine names (via !shortcut)
	Categories []string // explicitly selected categories (via !category)
	Language   string   // language from :lang syntax, or empty
}

// Parse parses a raw query string, extracting bang commands and language selectors.
// Bang syntax: !shortcut or !category (maps to searx/query.py BangParser)
// Language syntax: :en, :de, etc. (maps to searx/query.py LanguageParser)
func Parse(raw string, engines map[string]engine.Engine, knownCategories map[string]bool) Parsed {
	p := Parsed{}
	var queryParts []string

	tokens := strings.Fields(raw)
	for _, tok := range tokens {
		if strings.HasPrefix(tok, "!") && len(tok) > 1 {
			bang := tok[1:]
			if handleBang(&p, bang, engines, knownCategories) {
				continue
			}
		}
		if strings.HasPrefix(tok, ":") && len(tok) > 1 && len(tok) <= 6 {
			lang := tok[1:]
			if isLangCode(lang) {
				p.Language = lang
				continue
			}
		}
		queryParts = append(queryParts, tok)
	}

	p.Query = strings.Join(queryParts, " ")
	return p
}

// handleBang tries to match a bang token against engine shortcuts and categories.
// Returns true if the token was consumed.
func handleBang(p *Parsed, bang string, engines map[string]engine.Engine, knownCategories map[string]bool) bool {
	// Check engine shortcuts
	for _, eng := range engines {
		if eng.Shortcut() == bang {
			p.Engines = append(p.Engines, eng.Name())
			return true
		}
	}

	// Check engine names directly
	if _, ok := engines[bang]; ok {
		p.Engines = append(p.Engines, bang)
		return true
	}

	// Check categories
	lower := strings.ToLower(bang)
	if knownCategories[lower] {
		p.Categories = append(p.Categories, lower)
		return true
	}

	return false
}

// isLangCode returns true if the string looks like a language code (e.g., "en", "de", "zh-CN").
func isLangCode(s string) bool {
	if len(s) < 2 || len(s) > 5 {
		return false
	}
	for i, c := range s {
		if c == '-' && i > 0 {
			continue
		}
		if c >= 'a' && c <= 'z' {
			continue
		}
		if c >= 'A' && c <= 'Z' {
			continue
		}
		return false
	}
	return true
}
