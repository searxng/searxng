## What does this PR do?

This PR updates the parsing logic for both the `google` and `google_videos` engines to handle the modern HTML structure returned by Google when using GSA (Google Search App) User-Agents.

**Specific changes include:**
* **Google Videos (`gov`)**:
    * Updated title XPath to support `role="heading"`.
    * Improved URL extraction to correctly decode Google redirectors (`/url?q=...`) using `unquote`.
    * Added support for the `WRu9Cd` class to capture publication metadata (author/date).
    * Broadened thumbnail search and added a fallback to YouTube's `hqdefault.jpg`.
* **Google Web**:
    * Relaxed the strict snippet (`content`) requirement. Valid results are no longer discarded if a snippet is missing in the mobile UI.
    * Hardened URL extraction to handle both direct and redirected URLs safely.
    * Improved thumbnail extraction by searching the entire result block.

## Why is this change important?

Google recently changed the DOM structure for mobile-centric responses, causing the `google_videos` engine to return zero results and the main `google` engine to drop the majority of its results (due to missing snippets or failed URL parsing). These changes restore the functionality and improve the result count for both engines.

## How to test this PR locally?

Run a search using the engines directly via your local instance:
1. **Google Videos**: `http://localhost:8888/search?q=!gov+cute+puppies`
2. **Google Web**: `http://localhost:8888/search?q=cute+puppies&engines=google`

Verify that titles, URLs, snippets (where available), and thumbnails are correctly displayed.

## Author's checklist

- [x] Manual verification performed.
- [x] Python code formatted using `black`.

## Related issues
