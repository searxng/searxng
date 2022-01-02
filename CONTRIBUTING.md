# How to contribute

## Resources in the documentation

* [Development quickstart](https://docs.searxng.org/dev/contribution_guide.html)
* [Contribution guide](https://docs.searxng.org/dev/contribution_guide.html)

## Submitting PRs

Please follow the provided PR template when writing a description for your changes.

Do not take criticism personally. When you get feedback, it is about your work,
not your character, personality, etc. Keep in mind we all want to make the project better.

When something is not clear, please ask questions to clear things up.

If you would like to introduce a big architectural changes or do a refactoring
either in the codebase or the development tools, please open an issue with a proposal
first. This way we can think together about the problem and probably come up
with a better solution.

## Coding conventions and guidelines

### Commit messages

* Always write descriptive commit messages ("fix bug" is not acceptable).
* Use the present tense ("Add feature" not "Added feature").
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
* Limit the first line to 72 characters or less.
* Include the number of the issue you are fixing.

### Coding guidelines

As a Python project, we must follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) and [PEP 20](https://www.python.org/dev/peps/pep-0020/) guidelines.

Furthermore, follow the Clean code conventions. The most important
in this project are the following rules:

* Simpler is better. [KISS principle](https://en.wikipedia.org/wiki/KISS_principle)
* Be consistent.
* Every function must do one thing.
* Use descriptive names for functions and variables.
* Always look for the root cause.
* Keep configurable data high level.
* Avoid negative conditionals.
* Prefer fewer arguments.
* Do not add obvious comment to code.
* Do not comment out code, just delete lines.

