# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

SearXNG is a metasearch engine that aggregates results from multiple search engines while protecting user privacy. It's written primarily in Python with Flask as the web framework, using Jinja2 templates and supporting multiple themes.

## Development Commands

### Setup and Installation
- `make install` - Install SearXNG in development virtualenv (creates `local/py3` virtualenv)
- `./manage pyenv.install` - Same as above
- `make uninstall` or `./manage pyenv.uninstall` - Remove development installation

### Running the Application
- `make run` - Start development server on http://127.0.0.1:8888 with auto-reload enabled
- `./manage webapp.run` - Same as above (uses Granian WSGI server with hot reload)

### Testing
- `make test` - Run all tests (yamllint, black, pyright, pylint, unit, robot, rst, shell, shfmt)
- `./manage test.unit` - Run unit tests only
- `./manage test.robot` - Run robot (end-to-end) tests
- `./manage test.pylint` - Run pylint on codebase
- `./manage test.black` - Check Python code formatting with Black
- `./manage test.pyright` - Run type checking with Pyright
- `./manage test.pyright_modified` - Type check only modified files
- `./manage test.yamllint` - Lint YAML files

### Code Formatting
- `make format` - Format all code (Python and shell)
- `./manage format.python` - Format Python code with Black (line length: 120, target: py311)
- `./manage format.shell` - Format shell scripts with shfmt

### Search Engine Testing
- `./manage search.checker` - Test all search engines
- `./manage search.checker.<engine_name>` - Test specific engine (replace spaces with underscores in engine name)

### Themes and Frontend
- `./manage themes.all` - Build all themes
- `./manage themes.simple` - Build the 'simple' theme specifically
- `./manage themes.test` - Test theme builds
- `./manage themes.lint` - Lint theme code
- `./manage node.env.dev` - Set up Node.js development environment

### Documentation
- `./manage docs.html` - Build HTML documentation
- `./manage docs.live` - Auto-rebuild documentation while editing
- `./manage docs.clean` - Clean documentation build artifacts

### Container/Docker
- `./manage container.build` - Build container image
- `./manage container.test` - Test container build
- `./manage docker.build` - Build Docker image specifically

### Data Management
- `./manage data.all` - Fetch all data (traits, useragents, locales, currencies)
- `./manage data.traits` - Fetch engine traits data
- `./manage data.currencies` - Fetch currency data

## Architecture Overview

### Core Components

**Webapp Layer** (`searx/webapp.py`)
- Flask application serving as the main entry point
- Handles HTTP requests, routing, and response rendering
- Integrates with all other components (search, plugins, preferences, etc.)
- Uses WhiteNoise for static file serving

**Search Layer** (`searx/search/`)
- `SearchWithPlugins` class orchestrates the search workflow
- Supports external bangs (redirects like `!g query`)
- Integrates answerers (instant answers) and standard engine searches
- Multi-threaded request execution with timeout handling
- Search flow: external bang check → answerers → engine processors

**Engine Processors** (`searx/search/processors/`)
- `EngineProcessor` (abstract base class) defines processor interface
- `online.OnlineProcessor` - For web-based search engines
- `offline.OfflineProcessor` - For local/database engines  
- `online_currency`, `online_dictionary`, `online_url_search` - Specialized processors
- Processors handle initialization, parameter building, result fetching, and error handling
- Suspension system temporarily disables failing engines

**Engines** (`searx/engines/`)
- 200+ search engine implementations
- Each engine is a Python module with specific functions:
  - `request()` - Build search request parameters
  - `response()` - Parse engine response and return results
  - Optional `init()` - Initialize engine on startup
- Engine types: online, offline, online_url_search, online_currency, online_dictionary
- Configuration via `searx/settings.yml` under `engines:` section

**Result Types** (`searx/result_types/`)
- Type-safe result system replacing legacy dict-based results
- `EngineResults` - Container returned by engines
- Typed results: `Answer`, `MainResult`, `KeyValue`, `Code`, `Paper`, `File`, `WeatherAnswer`
- `ResultContainer` (`searx/results.py`) aggregates results from multiple engines

**Plugins** (`searx/plugins/`)
- Extend functionality via hooks: `pre_search`, `post_search`, `on_result`
- Loaded via `PluginStorage.STORAGE` singleton
- Can modify queries, filter results, add answers

**Settings System** (`searx/settings_loader.py`, `searx/settings_defaults.py`)
- YAML-based configuration (`searx/settings.yml`)
- Schema validation and defaults via `apply_schema()`
- Global `settings` dict accessible via `searx.get_setting()`
- Environment variable overrides (e.g., `SEARXNG_DEBUG`, `SEARXNG_PORT`)

**Localization** (`searx/locales.py`, `searx/sxng_locales.py`)
- Flask-Babel for translations
- Locale matching and selection via `localeselector()`
- Translation files in `searx/translations/`

### Key Design Patterns

**Engine Traits** (`searx/enginelib/traits.py`)
- `EngineTraits` stores engine capabilities (supported languages, regions, etc.)
- `fetch_traits()` function in engines discovers available options
- Used for locale/region mapping

**Caching** (`searx/cache.py`, `searx/enginelib/`)
- `EngineCache` - SQLite-based persistent cache with expiration
- Used for storing intermediate data (e.g., DDG's vqd tokens)

**Network Layer** (`searx/network/`)
- httpx-based async HTTP client
- Supports HTTP/2, SOCKS proxies, custom certificates
- Network contexts for connection pooling per engine

**Bot Detection** (`searx/botdetection/`)
- Link tokens for CSRF protection
- IP-based rate limiting via `searx/limiter.py`
- ProxyFix for handling reverse proxy headers

## Code Standards

### Python Conventions
- Python 3.10+ required (type hints using modern syntax)
- Line length: 120 characters
- Black formatting with `--skip-string-normalization`
- PEP 8 and PEP 20 compliance
- Pylint for linting (config: `.pylintrc`)
- Pyright for type checking (config: `pyrightconfig.json`)
- Virtualenv location: `local/py3/` (gitignored)

### Commit Messages
- Use present tense, imperative mood: "Add feature" not "Added feature"
- First line ≤72 characters
- Always descriptive (no "fix bug" messages)
- Include co-author line: `Co-Authored-By: Warp <agent@warp.dev>`

### Testing Requirements
- Write unit tests in `tests/unit/` using `SearxTestCase` base class
- Robot tests for end-to-end scenarios in `tests/robot/`
- Test settings in `tests/unit/settings/`
- All tests must pass before committing

### Engine Development
- Return `EngineResults` from `response()` function, not legacy dicts
- Use typed results: `res.types.MainResult()`, `res.types.Answer()`, etc.
- Implement proper error handling (will trigger suspension on repeated failures)
- Add engine traits via `fetch_traits()` for language/region support
- Document engine metadata in `about` dict

## Important File Locations

- **Main settings**: `searx/settings.yml`
- **Engine implementations**: `searx/engines/`
- **Templates**: `searx/templates/` (theme-specific subdirs)
- **Static files**: `searx/static/` (built from `client/`)
- **Translations**: `searx/translations/`
- **Utility scripts**: `utils/*.sh` (sourced by `./manage`)
- **Test configs**: `tests/unit/settings/`

## Environment Variables

- `SEARXNG_DEBUG=1` - Enable debug mode (colored logs, detailed output)
- `SEARXNG_SETTINGS_PATH` - Override settings file location
- `SEARXNG_PORT` - Override server port (default: 8888)
- `SEARXNG_BIND_ADDRESS` - Override bind address
- `SEARXNG_SECRET` - Override secret key
- `SEARXNG_VALKEY_URL` - Valkey/Redis connection URL

## Special Notes

- Never commit changes without explicit user request
- The `./manage` script is the central command dispatcher - it sources library scripts from `utils/` and provides 100+ subcommands
- Granian (WSGI server) is used for development with hot reload enabled
- The virtualenv path is `local/py3` - all Python commands run via `./manage pyenv.cmd <command>`
- When adding new engines, update `searx/settings.yml` engines list
- Theme development requires Node.js (managed via nvm)
- Static assets are built via `./manage static.build.commit`
