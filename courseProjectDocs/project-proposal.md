# Project Proposal

## Project Overview
Over the course of this semester we will be expanding the software testing capabilities of the SearXNG project. We will first be analyzing the existing testing frameworks using a custom script to collect [key quality metrics](#Key-Quality-Metrics). Once we have collected data on the current testing environment we will decide on what quality metrics we wish to expand using the testing concepts discussed in SWEN 777. While deciding what metrics, we will keep in mind the core ethos of the SearXNG project which is a decentralized, private search engine. Our additional tests will adhear to this and help enforce the ethos.

## Key Quality Metrics

### Maintainability
1. Code Structure
    - Lines of Code (LOC) per file/module
    - Comment density (comments / total lines)
    - Cyclomatic Complexity
2. Testability
    - Number of unit test cases / test suites
    - Test coverage

### Future Metrics

#### Deployability
The SearXNG developers suggest that a self-hosted instance of the search engine is the best way to use the project. We will test the ease of deployability through automated tests that build instances of the project using their documented steps.

#### Privacy
SearXNG is a **private** search engine, to make this claim less of a promise and more of a fact, we will create integration / security tests that detect any outgoing calls and analyze those calls for personally identifiable information. Tests for privacy will create quicker review cycles as new search providers can be quickly and deterministically audited for the information they provide to external services.
