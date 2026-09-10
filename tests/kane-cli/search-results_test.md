# SearXNG — search returns results

A Kane CLI natural-language end-to-end test that runs a search on a SearXNG
instance and verifies results are returned. Runs in a real browser (Kane CLI
also automates mobile apps on the iOS Simulator and Android Emulator).

Note: the run targets a public SearXNG instance (https://priv.au) so it can be
reproduced without a local deploy. Point it at any instance you host.

## Run a search and verify results
Go to https://priv.au.
Wait for the SearXNG search page.
Click the search box and type "open source software".
Press Enter to submit.
Wait for the results page to load.
Assert that at least one search result with a title and link is shown.
