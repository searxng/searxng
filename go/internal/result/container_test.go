package result

import (
	"testing"
)

func TestAddAndDedup(t *testing.T) {
	c := NewContainer()

	// Add two results with same URL from different engines.
	c.Add(Result{
		URL:      "https://example.com/page",
		Title:    "Short",
		Content:  "Brief content",
		Template: "default",
		Priority: "normal",
		Weight:   1.0,
	}, "google", 1)

	c.Add(Result{
		URL:      "https://example.com/page",
		Title:    "Longer Title Here",
		Content:  "A much longer and more detailed content description",
		Template: "default",
		Priority: "normal",
		Weight:   1.0,
	}, "bing", 2)

	results := c.GetOrderedResults()
	if len(results) != 1 {
		t.Fatalf("expected 1 deduped result, got %d", len(results))
	}

	r := results[0]
	// Should keep the longer title.
	if r.Title != "Longer Title Here" {
		t.Errorf("expected longer title, got %q", r.Title)
	}
	// Should keep the longer content.
	if r.Content != "A much longer and more detailed content description" {
		t.Errorf("expected longer content, got %q", r.Content)
	}
	// Should have both engines.
	if len(r.Engines) != 2 {
		t.Errorf("expected 2 engines, got %d: %v", len(r.Engines), r.Engines)
	}
	// Should have both positions.
	if len(r.Positions) != 2 {
		t.Errorf("expected 2 positions, got %d", len(r.Positions))
	}
}

func TestScoring(t *testing.T) {
	r := &Result{
		Positions: []int{1, 3},
		Weight:    1.0,
		Priority:  "normal",
	}
	r.CalculateScore()

	// score = 1.0/1 + 1.0/3 = 1.333...
	expected := 1.0 + 1.0/3.0
	if r.Score < expected-0.01 || r.Score > expected+0.01 {
		t.Errorf("expected score ~%.3f, got %.3f", expected, r.Score)
	}
}

func TestScoringHighPriority(t *testing.T) {
	r := &Result{
		Positions: []int{1, 5},
		Weight:    2.0,
		Priority:  "high",
	}
	r.CalculateScore()

	// score = 2.0 + 2.0 = 4.0
	if r.Score != 4.0 {
		t.Errorf("expected score 4.0, got %.3f", r.Score)
	}
}

func TestScoringLowPriority(t *testing.T) {
	r := &Result{
		Positions: []int{1},
		Weight:    1.0,
		Priority:  "low",
	}
	r.CalculateScore()

	if r.Score != 0.0 {
		t.Errorf("expected score 0.0, got %.3f", r.Score)
	}
}

func TestHTTPSPreferred(t *testing.T) {
	c := NewContainer()

	c.Add(Result{
		URL:      "http://example.com/page",
		Title:    "Test",
		Template: "default",
		Priority: "normal",
		Weight:   1.0,
	}, "engine1", 1)

	c.Add(Result{
		URL:      "https://example.com/page",
		Title:    "Test",
		Template: "default",
		Priority: "normal",
		Weight:   1.0,
	}, "engine2", 1)

	results := c.GetOrderedResults()
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if results[0].URL != "https://example.com/page" {
		t.Errorf("expected HTTPS URL, got %s", results[0].URL)
	}
}

func TestSuggestionDedup(t *testing.T) {
	c := NewContainer()
	c.AddSuggestion("test query")
	c.AddSuggestion("test query")
	c.AddSuggestion("different")

	if len(c.Suggestions) != 2 {
		t.Errorf("expected 2 suggestions, got %d", len(c.Suggestions))
	}
}

func TestAnswerDedup(t *testing.T) {
	c := NewContainer()
	c.AddAnswer(Answer{Answer: "42"})
	c.AddAnswer(Answer{Answer: "42"})
	c.AddAnswer(Answer{Answer: "other"})

	if len(c.Answers) != 2 {
		t.Errorf("expected 2 answers, got %d", len(c.Answers))
	}
}

func TestOrdering(t *testing.T) {
	c := NewContainer()

	// Result with high score (position 1, weight 2).
	c.Add(Result{
		URL:      "https://top.com",
		Title:    "Top Result",
		Template: "default",
		Priority: "normal",
		Weight:   2.0,
	}, "google", 1)

	// Result with lower score (position 5, weight 1).
	c.Add(Result{
		URL:      "https://low.com",
		Title:    "Low Result",
		Template: "default",
		Priority: "normal",
		Weight:   1.0,
	}, "bing", 5)

	results := c.GetOrderedResults()
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}

	// Higher score should be first.
	if results[0].URL != "https://top.com" {
		t.Errorf("expected top.com first, got %s", results[0].URL)
	}
	if results[1].URL != "https://low.com" {
		t.Errorf("expected low.com second, got %s", results[1].URL)
	}
}
