// Package config handles YAML configuration loading for the SearXNG Go server.
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"gopkg.in/yaml.v3"
)

// Config is the top-level configuration.
type Config struct {
	General  GeneralConfig  `yaml:"general"`
	Search   SearchConfig   `yaml:"search"`
	Server   ServerConfig   `yaml:"server"`
	Outgoing OutgoingConfig `yaml:"outgoing"`
	Engines  []EngineConfig `yaml:"engines"`
}

type GeneralConfig struct {
	Debug        bool   `yaml:"debug"`
	InstanceName string `yaml:"instance_name"`
}

type SearchConfig struct {
	SafeSearch          int    `yaml:"safe_search"`
	DefaultLang         string `yaml:"default_lang"`
	MaxPage             int    `yaml:"max_page"`
	AutocompleteBackend string `yaml:"autocomplete"`
}

type ServerConfig struct {
	Port        int    `yaml:"port"`
	BindAddress string `yaml:"bind_address"`
	SecretKey   string `yaml:"secret_key"`
	BaseURL     string `yaml:"base_url"`
}

type OutgoingConfig struct {
	RequestTimeout    float64  `yaml:"request_timeout"`
	MaxRequestTimeout float64  `yaml:"max_request_timeout"`
	UseHTTP2          bool     `yaml:"use_http2"`
	Proxies           []string `yaml:"proxies"`
	MaxConnections    int      `yaml:"pool_connections"`
	MaxIdleConns      int      `yaml:"pool_maxsize"`
	UserAgent         string   `yaml:"useragent"`
}

type EngineConfig struct {
	Name             string         `yaml:"name"`
	Engine           string         `yaml:"engine"`
	Shortcut         string         `yaml:"shortcut"`
	Categories       []string       `yaml:"categories"`
	Disabled         bool           `yaml:"disabled"`
	Inactive         bool           `yaml:"inactive"`
	Timeout          float64        `yaml:"timeout"`
	Weight           float64        `yaml:"weight"`
	Paging           bool           `yaml:"paging"`
	MaxPage          int            `yaml:"max_page"`
	SafeSearch       bool           `yaml:"safesearch"`
	TimeRangeSupport bool           `yaml:"time_range_support"`
	EnableHTTP       bool           `yaml:"enable_http"`
	Tokens           []string       `yaml:"tokens"`
	Extra            map[string]any `yaml:",inline"`
}

// TimeoutDuration returns the engine timeout as a time.Duration.
func (e *EngineConfig) TimeoutDuration() time.Duration {
	if e.Timeout <= 0 {
		return 0
	}
	return time.Duration(e.Timeout * float64(time.Second))
}

// Defaults returns a Config with sensible default values.
func Defaults() *Config {
	return &Config{
		General: GeneralConfig{
			Debug:        false,
			InstanceName: "SearXNG",
		},
		Search: SearchConfig{
			SafeSearch:  0,
			DefaultLang: "auto",
			MaxPage:     0,
		},
		Server: ServerConfig{
			Port:        8888,
			BindAddress: "127.0.0.1",
		},
		Outgoing: OutgoingConfig{
			RequestTimeout:    3.0,
			MaxRequestTimeout: 10.0,
			MaxConnections:    100,
			MaxIdleConns:      10,
		},
	}
}

// Load reads a YAML config file and returns the parsed Config.
// It checks SEARXNG_SETTINGS_PATH env var first, then falls back to the given path.
func Load(defaultPath string) (*Config, error) {
	path := os.Getenv("SEARXNG_SETTINGS_PATH")
	if path == "" {
		path = defaultPath
	}

	// If path is a directory, look for settings.yml inside it.
	info, err := os.Stat(path)
	if err != nil {
		return nil, fmt.Errorf("config path %q: %w", path, err)
	}
	if info.IsDir() {
		path = filepath.Join(path, "settings.yml")
	}

	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("reading config %q: %w", path, err)
	}

	cfg := Defaults()
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("parsing config %q: %w", path, err)
	}

	applyEngineDefaults(cfg)
	return cfg, nil
}

// applyEngineDefaults fills in missing engine fields with sensible defaults.
func applyEngineDefaults(cfg *Config) {
	for i := range cfg.Engines {
		e := &cfg.Engines[i]
		if e.Engine == "" {
			e.Engine = e.Name
		}
		if e.Shortcut == "" {
			e.Shortcut = "-"
		}
		if len(e.Categories) == 0 {
			e.Categories = []string{"general"}
		}
		if e.Timeout <= 0 {
			e.Timeout = cfg.Outgoing.RequestTimeout
		}
		if e.Weight <= 0 {
			e.Weight = 1.0
		}
	}
}

// ActiveEngines returns only engines that are not disabled or inactive.
func (c *Config) ActiveEngines() []EngineConfig {
	var active []EngineConfig
	for _, e := range c.Engines {
		if !e.Disabled && !e.Inactive {
			active = append(active, e)
		}
	}
	return active
}
