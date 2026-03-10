# SearXNG "Advanced" Theme - PR Overview

This document provides a comprehensive overview of the changes and new features introduced in the `theme-advanced` branch, compared to the `master` branch and the default "Simple" theme.

## 1. Feature Comparison: "Simple" vs. "Advanced"

| Feature | Description | Core Changes Required? | Files Affected |
| :--- | :--- | :--- | :--- |
| **Advanced Theme** | A new theme forked from "Simple" that introduces advanced media discovery and layout controls. | **Yes** (build scripts & settings) | `searx/templates/advanced/`, `client/advanced/`, `utils/lib_sxng_themes.sh`, `utils/lib_sxng_vite.sh` |
| **Dynamic Theme Toggle** | A persistent header toggle for Light/Dark/Black (OLED) modes. Remembers choice via a dedicated `preferred_dark_style` cookie. | **No** (Theme-only) | `searx/templates/advanced/base.html`, `client/advanced/src/js/util/cookies.ts` |
| **Video Grid View & Resizer** | A toggleable and resizable grid layout for video results, allowing users to adjust thumbnail sizes via a range slider. | **No** (Theme-only) | `client/advanced/src/less/style.less`, `searx/templates/advanced/results.html` |
| **Results per Page Selector** | Ability to fetch 10-50 results specifically for video searches, managed via a persistent setting. | **Yes** (Backend support) | `searx/search/models.py`, `searx/preferences.py`, `searx/webapp.py`, `searx/search/processors/abstract.py` |
| **Google Videos Multi-fetch** | Refactored the `google_videos` engine to perform multiple asynchronous requests to fulfill higher result counts. | **Yes** (Engine update) | `searx/engines/google_videos.py` |
| **Enhanced Pagination** | Pagination forms now maintain the user's `results_per_page` setting across page navigation. | **No** (Theme-only) | `searx/templates/advanced/results.html` |
| **Adaptive "Back to Top"** | Enhances the existing "Back to Top" functionality by dynamically adjusting its position when switching between list and grid layouts in video results. | **No** (Theme-only) | `client/advanced/src/less/style.less`, `searx/templates/advanced/results.html` |

---

## 2. Draft Pull Request

### What does this PR do?

This PR introduces the **Advanced** theme to SearXNG, forked from the default "Simple" theme, with several enhancements focused on media discovery and advanced layout control. Key changes include:
- **Advanced Media Layouts**: A new resizable grid view for video results, including a UI toggle and a range slider for thumbnail size adjustments.
- **Results per Page (Video)**: Implementation of a "Results per Page" selector (10-50) for video searches.
- **Engine Multi-fetch Capability**: The `google_videos` engine has been refactored to perform multiple asynchronous fetches to aggregate higher result counts as requested by the user.
- **Dynamic Theme Management**: A header toggle allowing users to switch between Light, Dark, and Black (OLED) modes dynamically.
- **Persistent Settings in Pagination**: Enhanced pagination forms to ensure the `results_per_page` setting persists across searches and page navigation.
- **Adaptive UI**: The "Back to Top" button now adjusts its position dynamically to accommodate different layouts (list vs. grid) in video results.
- **Backend Integration**: Core updates to `search.models`, `preferences`, and the `abstract` engine processor to natively handle the `results_per_page` parameter.

### Why is this change important?

The "Advanced" theme provides a more powerful and customizable interface for media discovery. By enabling native grid resizing and high-volume result fetching for videos, SearXNG becomes a more versatile tool for power users without compromising privacy or the clean aesthetic of the original design.

### How to test this PR locally?

1. Build the new theme:
   ```bash
   ./manage themes.all
   ```
2. Start the SearXNG instance:
   ```bash
   ./manage webapp.run
   ```
3. Navigate to Preferences and select the **Advanced** theme.
4. Test the **Theme Toggle** and its persistence via cookies.
5. Perform a video search:
   - Use the **Results per Page** dropdown to fetch 50 results.
   - Use the **Grid View Toggle** and **Resizer** to adjust the layout.
   - Verify that **Pagination** maintains the results per page setting.
   - Check that the **Back to Top** button remains accessible in both list and grid views.

### Author's checklist

- [x] All code formatted with `black`.
- [x] Frontend linting and formatting (`biome`, `stylelint`) passed in `client/advanced`.
- [x] Multi-fetch engine logic verified.
- [x] Setting persistence verified across pagination.

### Related issues

None.
