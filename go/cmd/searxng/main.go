// SearXNG-Go is a metasearch engine that aggregates results from
// multiple search engines and returns JSON results.
package main

import (
	"flag"
	"fmt"
	"log/slog"
	"os"
	"sort"

	"github.com/searxng/searxng-go/internal/config"
	"github.com/searxng/searxng-go/internal/engine"
	"github.com/searxng/searxng-go/internal/network"
	"github.com/searxng/searxng-go/internal/server"

	// Import engine packages to trigger their init() registration.
	_ "github.com/searxng/searxng-go/internal/engines/bing"
	_ "github.com/searxng/searxng-go/internal/engines/brave"
	_ "github.com/searxng/searxng-go/internal/engines/duckduckgo"
	_ "github.com/searxng/searxng-go/internal/engines/google"
	_ "github.com/searxng/searxng-go/internal/engines/wikipedia"
)

func main() {
	configPath := flag.String("config", "settings.yml", "path to settings YAML file")
	flag.Parse()

	// Set up structured logging.
	logLevel := slog.LevelInfo

	cfg, err := config.Load(*configPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error loading config: %v\n", err)
		os.Exit(1)
	}

	if cfg.General.Debug {
		logLevel = slog.LevelDebug
	}
	slog.SetDefault(slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: logLevel})))

	slog.Info("loaded configuration",
		"instance", cfg.General.InstanceName,
		"engines_configured", len(cfg.Engines),
		"debug", cfg.General.Debug,
	)

	// Report registered engine types.
	types := engine.RegisteredTypes()
	sort.Strings(types)
	slog.Info("registered engine types", "types", types)

	// Load engines from config.
	engines, err := engine.LoadEngines(cfg.Engines)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error loading engines: %v\n", err)
		os.Exit(1)
	}

	slog.Info("engines loaded", "active", len(engines))
	for name := range engines {
		slog.Debug("engine active", "name", name)
	}

	// Create HTTP client for upstream engine requests.
	client := network.NewClient(cfg.Outgoing)

	// Create and start the HTTP server.
	srv := server.New(cfg, engines, client)
	slog.Info("starting SearXNG-Go",
		"addr", fmt.Sprintf("%s:%d", cfg.Server.BindAddress, cfg.Server.Port),
	)

	if err := srv.ListenAndServe(); err != nil {
		fmt.Fprintf(os.Stderr, "server error: %v\n", err)
		os.Exit(1)
	}
}
