package engine

import (
	"fmt"
	"log/slog"
	"sync"

	"github.com/searxng/searxng-go/internal/config"
)

// Factory creates an Engine from configuration.
type Factory func(cfg config.EngineConfig) (Engine, error)

var (
	mu        sync.RWMutex
	factories = make(map[string]Factory)
)

// Register registers an engine factory for the given engine type name.
// Typically called from init() in engine implementation packages.
func Register(engineType string, factory Factory) {
	mu.Lock()
	defer mu.Unlock()
	if _, exists := factories[engineType]; exists {
		panic(fmt.Sprintf("engine type %q already registered", engineType))
	}
	factories[engineType] = factory
}

// LoadEngines creates engine instances from config, skipping disabled/inactive engines.
func LoadEngines(configs []config.EngineConfig) (map[string]Engine, error) {
	mu.RLock()
	defer mu.RUnlock()

	engines := make(map[string]Engine)
	for _, cfg := range configs {
		if cfg.Disabled || cfg.Inactive {
			continue
		}

		factory, ok := factories[cfg.Engine]
		if !ok {
			slog.Warn("no factory registered for engine type, skipping",
				"engine", cfg.Name, "type", cfg.Engine)
			continue
		}

		eng, err := factory(cfg)
		if err != nil {
			slog.Error("failed to create engine, skipping",
				"engine", cfg.Name, "error", err)
			continue
		}

		engines[cfg.Name] = eng
		slog.Debug("loaded engine", "name", cfg.Name, "type", cfg.Engine,
			"categories", cfg.Categories)
	}

	return engines, nil
}

// RegisteredTypes returns the names of all registered engine types.
func RegisteredTypes() []string {
	mu.RLock()
	defer mu.RUnlock()
	types := make([]string, 0, len(factories))
	for t := range factories {
		types = append(types, t)
	}
	return types
}
