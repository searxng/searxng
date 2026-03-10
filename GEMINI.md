# SearXNG Project Instructions

This project is SearXNG, a privacy-respecting, open metasearch engine that aggregates results from various search engines without tracking or profiling users.

## Project Overview

- **Purpose**: Privacy-focused metasearch engine.
- **Main Technologies**:
  - **Backend**: Python (Flask framework), Jinja2 (templating), HTTPX (async networking), LXML (HTML parsing).
  - **Frontend**: Vite, TypeScript, Less (styles), Biome (linting/formatting).
  - **Data/Cache**: Valkey (Redis-compatible) for caching and limiter.
  - **Deployment**: Support for Docker/Podman, systemd, and various web servers (Granian, uWSGI, etc.).

## Directory Structure

- `searx/`: Core Python application code.
  - `engines/`: Implementation of search engine scrapers/API integrations.
  - `templates/`: Jinja2 templates for the UI.
  - `static/`: Static assets (built theme files, etc.).
- `client/`: Frontend source code.
  - `simple/`: The default "Simple" theme (Vite-based).
- `tests/`: Unit and integration tests (Robot Framework).
- `utils/`: Shell scripts and libraries for development and deployment.
- `manage`: Primary entry point for development tasks.

## Building and Running

The project uses a `./manage` script to orchestrate most development tasks.

### Development Server
- **Run app**: `./manage webapp.run`
  - Runs on `http://127.0.0.1:8888` by default.
  - In the provided dev environment, it is often exposed on `http://localhost:8889`.
  - Uses `Granian` as the WSGI server with auto-reload enabled.

### Environment Setup
- **Install dependencies**: `./manage pyenv.install` (sets up virtualenv).
- **Frontend build**: Vite is used for theme building.
  - Commands available in `client/simple/package.json`: `npm run build`, `npm run build:vite`.

### Quality and Testing
- **Formatting**:
  - Python: `./manage format.python` (uses `black`).
  - Shell: `./manage format.shell` (uses `shfmt`).
- **Linting**:
  - Frontend: `npm run lint` in `client/simple`.
- **Testing**:
  - Unit tests: `./manage test.unit` or `pytest`.
  - Full test suite: `./manage test.all`.

## Development Conventions

- **Coding Style**:
  - Follow **PEP 8** and **PEP 20** for Python.
  - Adhere to **Clean Code** principles: descriptive names, single-responsibility functions, and "KISS" (Keep It Simple, Stupid).
- **Commit Messages**:
  - Use descriptive titles.
  - Present tense, imperative mood (e.g., "Add feature", not "Added feature").
  - First line length limit: 72 characters.
- **Architecture**:
  - Engines are modular and located in `searx/engines/`.
  - Themes are structured with source code in `client/` and output in `searx/static/themes/`.
- **Instructional Context**:
  - Always check `searx/settings.yml` for default configurations.
  - Use the `./manage` script whenever possible for environment-consistent actions.
