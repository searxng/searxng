package network

import (
	"sync"
	"time"
)

// SuspendedStatus tracks consecutive errors for an engine
// and suspends it for escalating periods.
type SuspendedStatus struct {
	mu              sync.Mutex
	consecutiveErrs int
	suspendedUntil  time.Time
	banTimeOnFail   time.Duration
	maxBanTime      time.Duration
}

// NewSuspendedStatus creates a suspension tracker.
func NewSuspendedStatus(banTimeOnFail, maxBanTime time.Duration) *SuspendedStatus {
	if banTimeOnFail <= 0 {
		banTimeOnFail = 30 * time.Second
	}
	if maxBanTime <= 0 {
		maxBanTime = 10 * time.Minute
	}
	return &SuspendedStatus{
		banTimeOnFail: banTimeOnFail,
		maxBanTime:    maxBanTime,
	}
}

// IsSuspended returns true if the engine is currently suspended.
func (s *SuspendedStatus) IsSuspended() bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	return time.Now().Before(s.suspendedUntil)
}

// RecordSuccess resets the consecutive error counter.
func (s *SuspendedStatus) RecordSuccess() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.consecutiveErrs = 0
	s.suspendedUntil = time.Time{}
}

// RecordError increments the error counter and potentially suspends the engine.
func (s *SuspendedStatus) RecordError() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.consecutiveErrs++

	// Escalating ban: banTimeOnFail * consecutiveErrors, capped at maxBanTime.
	banDuration := s.banTimeOnFail * time.Duration(s.consecutiveErrs)
	if banDuration > s.maxBanTime {
		banDuration = s.maxBanTime
	}
	s.suspendedUntil = time.Now().Add(banDuration)
}

// SuspendFor suspends the engine for a specific duration (e.g., CAPTCHA).
func (s *SuspendedStatus) SuspendFor(d time.Duration) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.consecutiveErrs++
	s.suspendedUntil = time.Now().Add(d)
}

// ConsecutiveErrors returns the current error count.
func (s *SuspendedStatus) ConsecutiveErrors() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.consecutiveErrs
}
