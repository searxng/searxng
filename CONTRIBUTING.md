# Contributing to SearXNG Improved

Thank you for your interest in contributing! This guide covers the basics.

## Getting Started

1. **Fork** the repository and clone your fork
2. Create a **feature branch**: `git checkout -b feature/my-change`
3. Make your changes and **commit** with clear messages
4. **Push** your branch and open a Pull Request

## Development Setup

```bash
make install  # Install dependencies
make run      # Run the development server
make test     # Run the test suite
```

## Code Style

- Follow **PEP 8** with a max line length of 120
- Use **Black** for formatting and **isort** for import sorting
- Run **flake8** for linting before submitting
- Pre-commit hooks are configured — install them:
  ```bash
  pip install pre-commit
  pre-commit install
  ```

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation change
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Maintenance

## Pull Requests

- Keep PRs **focused** on a single change
- Include tests for new functionality
- Update documentation when needed
- Follow the PR template

## Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version, etc.)

## License

By contributing, you agree that your contributions will be licensed under the AGPLv3+.