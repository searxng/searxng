package result

import (
	"sort"
	"sync"
)

// Container collects results from multiple engines and handles
// deduplication, merging, scoring, and ranking.
type Container struct {
	mu sync.Mutex

	mainResults map[string]*Result // keyed by result hash
	Answers     []Answer
	Suggestions []Suggestion
	Corrections []Correction
	Infoboxes   []map[string]any
	Unresponsive []UnresponsiveEngine
	NumberOfResults int
}

// NewContainer creates an empty result container.
func NewContainer() *Container {
	return &Container{
		mainResults: make(map[string]*Result),
	}
}

// Add adds a single result to the container. Safe for concurrent use.
func (c *Container) Add(r Result, engineName string, position int) {
	c.mu.Lock()
	defer c.mu.Unlock()

	r.Engine = engineName
	if len(r.Engines) == 0 {
		r.Engines = []string{engineName}
	}
	if len(r.Positions) == 0 {
		r.Positions = []int{position}
	}
	if r.Priority == "" {
		r.Priority = "normal"
	}

	hash := r.Hash()
	if existing, ok := c.mainResults[hash]; ok {
		existing.Merge(&r)
	} else {
		c.mainResults[hash] = &r
	}
}

// AddResults adds a batch of results from an engine.
func (c *Container) AddResults(results []Result, engineName string) {
	for i, r := range results {
		c.Add(r, engineName, i+1)
	}
}

// AddAnswer adds an instant answer.
func (c *Container) AddAnswer(a Answer) {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Deduplicate answers
	for _, existing := range c.Answers {
		if existing.Answer == a.Answer {
			return
		}
	}
	c.Answers = append(c.Answers, a)
}

// AddSuggestion adds a search suggestion.
func (c *Container) AddSuggestion(s string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	for _, existing := range c.Suggestions {
		if existing == s {
			return
		}
	}
	c.Suggestions = append(c.Suggestions, s)
}

// AddCorrection adds a spelling correction.
func (c *Container) AddCorrection(s string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	for _, existing := range c.Corrections {
		if existing == s {
			return
		}
	}
	c.Corrections = append(c.Corrections, s)
}

// AddUnresponsive records an engine that failed.
func (c *Container) AddUnresponsive(engine, errMsg string, suspended bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.Unresponsive = append(c.Unresponsive, UnresponsiveEngine{
		Engine:    engine,
		Error:     errMsg,
		Suspended: suspended,
	})
}

// GetOrderedResults calculates scores, sorts, and groups results.
// Matches the Python ranking at searx/results.py:197-253.
func (c *Container) GetOrderedResults() []Result {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Collect all results and calculate scores.
	results := make([]Result, 0, len(c.mainResults))
	for _, r := range c.mainResults {
		r.CalculateScore()
		results = append(results, *r)
	}

	// Primary sort by score descending.
	sort.Slice(results, func(i, j int) bool {
		return results[i].Score > results[j].Score
	})

	// Group by category:template:has_image, max 8 per group.
	return groupResults(results)
}

// groupResults interleaves results by their category group key,
// preventing one category from dominating the result list.
func groupResults(sorted []Result) []Result {
	const maxPerGroup = 8
	const maxDistance = 20

	type groupState struct {
		count    int
		firstPos int
	}

	groups := make(map[string]*groupState)
	var output []Result

	for _, r := range sorted {
		key := resultGroupKey(r)
		g, exists := groups[key]
		if !exists {
			g = &groupState{firstPos: len(output)}
			groups[key] = g
		}

		if g.count >= maxPerGroup {
			continue
		}

		// Check distance constraint.
		insertPos := len(output)
		if exists && insertPos-g.firstPos > maxDistance {
			continue
		}

		output = append(output, r)
		g.count++
	}

	return output
}

func resultGroupKey(r Result) string {
	tmpl := r.Template
	if tmpl == "" {
		tmpl = "default"
	}
	imgPart := ""
	if r.ImgSrc != "" {
		imgPart = "img"
	}
	return r.Category + ":" + tmpl + ":" + imgPart
}
