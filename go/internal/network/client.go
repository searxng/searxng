// Package network provides HTTP client management for upstream engine requests.
package network

import (
	"context"
	"crypto/tls"
	"fmt"
	"io"
	"math/rand/v2"
	"net"
	"net/http"
	"time"

	"github.com/searxng/searxng-go/internal/config"
)

// Common desktop browser user agents for rotation.
var userAgents = []string{
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
	"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
	"Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
}

// Client wraps an HTTP client with engine-appropriate configuration.
type Client struct {
	httpClient *http.Client
	timeout    time.Duration
}

// NewClient creates a Client configured from OutgoingConfig.
func NewClient(cfg config.OutgoingConfig) *Client {
	transport := &http.Transport{
		DialContext: (&net.Dialer{
			Timeout:   30 * time.Second,
			KeepAlive: 30 * time.Second,
		}).DialContext,
		MaxIdleConns:          cfg.MaxConnections,
		MaxIdleConnsPerHost:   cfg.MaxIdleConns,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:  10 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
		TLSClientConfig:       &tls.Config{MinVersion: tls.VersionTLS12},
	}

	timeout := time.Duration(cfg.RequestTimeout * float64(time.Second))
	if timeout <= 0 {
		timeout = 5 * time.Second
	}

	return &Client{
		httpClient: &http.Client{
			Transport: transport,
			Timeout:   timeout,
		},
		timeout: timeout,
	}
}

// Do executes an HTTP request with the given context, returning the response and body.
// It automatically sets a random User-Agent if none is present.
func (c *Client) Do(ctx context.Context, req *http.Request) (*http.Response, []byte, error) {
	if req.Header.Get("User-Agent") == "" {
		req.Header.Set("User-Agent", RandomUserAgent())
	}

	req = req.WithContext(ctx)
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, nil, fmt.Errorf("http request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return resp, nil, fmt.Errorf("reading response body: %w", err)
	}

	return resp, body, nil
}

// RandomUserAgent returns a random browser user agent string.
func RandomUserAgent() string {
	return userAgents[rand.IntN(len(userAgents))]
}
