package network

import (
	"net/http"
	"strings"
)

// EngineError classifies an upstream engine error.
type EngineError struct {
	Kind    ErrorKind
	Message string
}

func (e *EngineError) Error() string { return e.Message }

// ErrorKind identifies the class of engine error.
type ErrorKind int

const (
	ErrorUnknown ErrorKind = iota
	ErrorTimeout
	ErrorAccessDenied
	ErrorTooManyRequests
	ErrorCaptcha
	ErrorCloudflare
	ErrorSSL
)

// ClassifyHTTPError inspects an HTTP response for known error patterns.
// Maps to searx/network/raise_for_httperror.py.
func ClassifyHTTPError(resp *http.Response, body []byte) *EngineError {
	if resp.StatusCode >= 200 && resp.StatusCode < 400 {
		return nil
	}

	bodyStr := string(body)

	// Cloudflare detection
	if isCloudflareChallenge(resp, bodyStr) {
		return &EngineError{Kind: ErrorCloudflare, Message: "cloudflare challenge detected"}
	}

	// CAPTCHA detection
	if isCaptcha(bodyStr) {
		return &EngineError{Kind: ErrorCaptcha, Message: "captcha detected"}
	}

	switch resp.StatusCode {
	case http.StatusTooManyRequests:
		return &EngineError{Kind: ErrorTooManyRequests, Message: "too many requests (429)"}
	case http.StatusForbidden:
		return &EngineError{Kind: ErrorAccessDenied, Message: "access denied (403)"}
	case http.StatusPaymentRequired:
		return &EngineError{Kind: ErrorAccessDenied, Message: "access denied (402)"}
	default:
		return &EngineError{Kind: ErrorUnknown, Message: http.StatusText(resp.StatusCode)}
	}
}

func isCloudflareChallenge(resp *http.Response, body string) bool {
	server := resp.Header.Get("Server")
	if !strings.Contains(strings.ToLower(server), "cloudflare") {
		return false
	}
	if resp.StatusCode == 403 || resp.StatusCode == 503 {
		return true
	}
	if strings.Contains(body, "challenges.cloudflare.com") {
		return true
	}
	return false
}

func isCaptcha(body string) bool {
	lower := strings.ToLower(body)
	return strings.Contains(lower, "recaptcha") ||
		strings.Contains(lower, "g-recaptcha") ||
		strings.Contains(lower, "hcaptcha")
}
